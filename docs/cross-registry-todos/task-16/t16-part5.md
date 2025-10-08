<!-- file: docs/cross-registry-todos/task-16/t16-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t16-deployment-automation-part5-w0x1y2z3-a4b5 -->

# Task 16 Part 5: Infrastructure as Code with Terraform and Pulumi

## Terraform Configuration

### Provider Configuration

```hcl
# file: terraform/providers.tf
# version: 1.0.0
# guid: terraform-providers

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }

    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }

    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ubuntu-autoinstall-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

provider "kubectl" {
  config_path = "~/.kube/config"
}

provider "aws" {
  region = var.aws_region
}
```

### Variables

```hcl
# file: terraform/variables.tf
# version: 1.0.0
# guid: terraform-variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "ubuntu-autoinstall"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "ubuntu-autoinstall-agent"
}

variable "app_version" {
  description = "Application version"
  type        = string
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 3
}

variable "image_repository" {
  description = "Container image repository"
  type        = string
  default     = "ghcr.io/jdfalk/ubuntu-autoinstall-agent"
}

variable "resource_limits" {
  description = "Resource limits for containers"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "500m"
    memory = "512Mi"
  }
}

variable "resource_requests" {
  description = "Resource requests for containers"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "250m"
    memory = "256Mi"
  }
}

variable "ingress_host" {
  description = "Ingress hostname"
  type        = string
}

variable "enable_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "hpa_min_replicas" {
  description = "Minimum replicas for HPA"
  type        = number
  default     = 3
}

variable "hpa_max_replicas" {
  description = "Maximum replicas for HPA"
  type        = number
  default     = 10
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
```

### Kubernetes Deployment Module

```hcl
# file: terraform/modules/kubernetes-app/main.tf
# version: 1.0.0
# guid: terraform-k8s-app-module

resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace

    labels = merge(
      var.labels,
      {
        environment = var.environment
        managed-by  = "terraform"
      }
    )
  }
}

resource "kubernetes_config_map" "app" {
  metadata {
    name      = "${var.app_name}-config"
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels
  }

  data = {
    "config.yaml" = yamlencode({
      server = {
        host    = "0.0.0.0"
        port    = 8080
        workers = 4
      }

      iso = {
        cache_dir = "/var/cache/ubuntu-autoinstall/isos"
        versions  = ["20.04", "22.04", "24.04"]
        architectures = ["amd64", "arm64"]
      }

      logging = {
        level  = var.log_level
        format = "json"
        output = "stdout"
      }
    })
  }
}

resource "kubernetes_secret" "app" {
  metadata {
    name      = "${var.app_name}-secrets"
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels
  }

  data = {
    database-url = var.database_url
  }
}

resource "kubernetes_deployment" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels

    annotations = {
      "deployment.kubernetes.io/revision" = var.app_version
    }
  }

  spec {
    replicas = var.enable_autoscaling ? null : var.replica_count

    strategy {
      type = "RollingUpdate"

      rolling_update {
        max_surge       = "25%"
        max_unavailable = "0"
      }
    }

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = merge(
          var.labels,
          {
            app     = var.app_name
            version = var.app_version
          }
        )

        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9090"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.app.metadata[0].name

        security_context {
          run_as_non_root = true
          run_as_user     = 1000
          fs_group        = 1000
        }

        container {
          name  = var.app_name
          image = "${var.image_repository}:${var.app_version}"

          port {
            name           = "http"
            container_port = 8080
            protocol       = "TCP"
          }

          port {
            name           = "metrics"
            container_port = 9090
            protocol       = "TCP"
          }

          env {
            name  = "RUST_LOG"
            value = var.log_level
          }

          env {
            name = "DATABASE_URL"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.app.metadata[0].name
                key  = "database-url"
              }
            }
          }

          resources {
            limits = {
              cpu    = var.resource_limits.cpu
              memory = var.resource_limits.memory
            }

            requests = {
              cpu    = var.resource_requests.cpu
              memory = var.resource_requests.memory
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = "http"
            }

            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = "http"
            }

            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/ubuntu-autoinstall"
            read_only  = true
          }
        }

        volume {
          name = "config"

          config_map {
            name = kubernetes_config_map.app.metadata[0].name
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      spec[0].replicas,  # Ignore if HPA is managing replicas
    ]
  }
}

resource "kubernetes_service" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = var.app_name
    }

    port {
      name        = "http"
      port        = 80
      target_port = "http"
      protocol    = "TCP"
    }

    port {
      name        = "metrics"
      port        = 9090
      target_port = "metrics"
      protocol    = "TCP"
    }
  }
}

resource "kubernetes_ingress_v1" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels

    annotations = {
      "kubernetes.io/ingress.class"                = "nginx"
      "cert-manager.io/cluster-issuer"             = "letsencrypt-prod"
      "nginx.ingress.kubernetes.io/ssl-redirect"   = "true"
      "nginx.ingress.kubernetes.io/rate-limit"     = "100"
    }
  }

  spec {
    tls {
      hosts       = [var.ingress_host]
      secret_name = "${var.app_name}-tls"
    }

    rule {
      host = var.ingress_host

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.app.metadata[0].name

              port {
                name = "http"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_account" "app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "app" {
  count = var.enable_autoscaling ? 1 : 0

  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app.metadata[0].name
    labels    = var.labels
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.app.metadata[0].name
    }

    min_replicas = var.hpa_min_replicas
    max_replicas = var.hpa_max_replicas

    metric {
      type = "Resource"

      resource {
        name = "cpu"

        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }

    metric {
      type = "Resource"

      resource {
        name = "memory"

        target {
          type                = "Utilization"
          average_utilization = 80
        }
      }
    }
  }
}
```

### Helm Release with Terraform

```hcl
# file: terraform/helm.tf
# version: 1.0.0
# guid: terraform-helm-release

resource "helm_release" "ubuntu_autoinstall_agent" {
  name       = "ubuntu-autoinstall-agent"
  namespace  = var.namespace
  chart      = "../helm/ubuntu-autoinstall-agent"
  version    = "1.0.0"

  create_namespace = true

  values = [
    templatefile("${path.module}/values/${var.environment}.yaml", {
      app_version   = var.app_version
      replica_count = var.replica_count
      ingress_host  = var.ingress_host
    })
  ]

  set_sensitive {
    name  = "secrets.databaseUrl"
    value = var.database_url
  }

  set {
    name  = "image.tag"
    value = var.app_version
  }

  set {
    name  = "replicaCount"
    value = var.replica_count
  }

  depends_on = [
    kubernetes_namespace.app
  ]
}
```

## Pulumi Infrastructure

### Pulumi TypeScript Program

```typescript
// file: pulumi/index.ts
// version: 1.0.0
// guid: pulumi-program

import * as pulumi from "@pulumi/pulumi";
import * as k8s from "@pulumi/kubernetes";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const environment = pulumi.getStack();

// Configuration
const appName = "ubuntu-autoinstall-agent";
const namespace = config.require("namespace");
const appVersion = config.require("appVersion");
const replicaCount = config.getNumber("replicaCount") || 3;
const ingressHost = config.require("ingressHost");
const databaseUrl = config.requireSecret("databaseUrl");

// Create namespace
const ns = new k8s.core.v1.Namespace(appName, {
  metadata: {
    name: namespace,
    labels: {
      environment: environment,
      "managed-by": "pulumi",
    },
  },
});

// Create ConfigMap
const configMap = new k8s.core.v1.ConfigMap(`${appName}-config`, {
  metadata: {
    name: `${appName}-config`,
    namespace: ns.metadata.name,
  },
  data: {
    "config.yaml": JSON.stringify({
      server: {
        host: "0.0.0.0",
        port: 8080,
        workers: 4,
      },
      iso: {
        cacheDir: "/var/cache/ubuntu-autoinstall/isos",
        versions: ["20.04", "22.04", "24.04"],
        architectures: ["amd64", "arm64"],
      },
      logging: {
        level: environment === "production" ? "warn" : "info",
        format: "json",
        output: "stdout",
      },
    }),
  },
});

// Create Secret
const secret = new k8s.core.v1.Secret(`${appName}-secret`, {
  metadata: {
    name: `${appName}-secret`,
    namespace: ns.metadata.name,
  },
  stringData: {
    "database-url": databaseUrl,
  },
});

// Create Deployment
const deployment = new k8s.apps.v1.Deployment(appName, {
  metadata: {
    name: appName,
    namespace: ns.metadata.name,
    labels: {
      app: appName,
    },
  },
  spec: {
    replicas: replicaCount,
    strategy: {
      type: "RollingUpdate",
      rollingUpdate: {
        maxSurge: "25%",
        maxUnavailable: 0,
      },
    },
    selector: {
      matchLabels: {
        app: appName,
      },
    },
    template: {
      metadata: {
        labels: {
          app: appName,
          version: appVersion,
        },
        annotations: {
          "prometheus.io/scrape": "true",
          "prometheus.io/port": "9090",
          "prometheus.io/path": "/metrics",
        },
      },
      spec: {
        securityContext: {
          runAsNonRoot: true,
          runAsUser: 1000,
          fsGroup: 1000,
        },
        containers: [
          {
            name: appName,
            image: `ghcr.io/jdfalk/ubuntu-autoinstall-agent:${appVersion}`,
            ports: [
              { name: "http", containerPort: 8080 },
              { name: "metrics", containerPort: 9090 },
            ],
            env: [
              { name: "RUST_LOG", value: "info" },
              {
                name: "DATABASE_URL",
                valueFrom: {
                  secretKeyRef: {
                    name: secret.metadata.name,
                    key: "database-url",
                  },
                },
              },
            ],
            resources: {
              limits: {
                cpu: "500m",
                memory: "512Mi",
              },
              requests: {
                cpu: "250m",
                memory: "256Mi",
              },
            },
            livenessProbe: {
              httpGet: {
                path: "/health",
                port: "http",
              },
              initialDelaySeconds: 30,
              periodSeconds: 10,
            },
            readinessProbe: {
              httpGet: {
                path: "/ready",
                port: "http",
              },
              initialDelaySeconds: 10,
              periodSeconds: 5,
            },
            volumeMounts: [
              {
                name: "config",
                mountPath: "/etc/ubuntu-autoinstall",
                readOnly: true,
              },
            ],
          },
        ],
        volumes: [
          {
            name: "config",
            configMap: {
              name: configMap.metadata.name,
            },
          },
        ],
      },
    },
  },
});

// Create Service
const service = new k8s.core.v1.Service(appName, {
  metadata: {
    name: appName,
    namespace: ns.metadata.name,
    labels: {
      app: appName,
    },
  },
  spec: {
    type: "ClusterIP",
    selector: {
      app: appName,
    },
    ports: [
      { name: "http", port: 80, targetPort: "http" },
      { name: "metrics", port: 9090, targetPort: "metrics" },
    ],
  },
});

// Create Ingress
const ingress = new k8s.networking.v1.Ingress(appName, {
  metadata: {
    name: appName,
    namespace: ns.metadata.name,
    annotations: {
      "kubernetes.io/ingress.class": "nginx",
      "cert-manager.io/cluster-issuer": "letsencrypt-prod",
      "nginx.ingress.kubernetes.io/ssl-redirect": "true",
    },
  },
  spec: {
    tls: [
      {
        hosts: [ingressHost],
        secretName: `${appName}-tls`,
      },
    ],
    rules: [
      {
        host: ingressHost,
        http: {
          paths: [
            {
              path: "/",
              pathType: "Prefix",
              backend: {
                service: {
                  name: service.metadata.name,
                  port: { name: "http" },
                },
              },
            },
          ],
        },
      },
    ],
  },
});

// Create HPA
const hpa = new k8s.autoscaling.v2.HorizontalPodAutoscaler(appName, {
  metadata: {
    name: appName,
    namespace: ns.metadata.name,
  },
  spec: {
    scaleTargetRef: {
      apiVersion: "apps/v1",
      kind: "Deployment",
      name: deployment.metadata.name,
    },
    minReplicas: 3,
    maxReplicas: 10,
    metrics: [
      {
        type: "Resource",
        resource: {
          name: "cpu",
          target: {
            type: "Utilization",
            averageUtilization: 70,
          },
        },
      },
      {
        type: "Resource",
        resource: {
          name: "memory",
          target: {
            type: "Utilization",
            averageUtilization: 80,
          },
        },
      },
    ],
  },
});

// Exports
export const namespaceName = ns.metadata.name;
export const deploymentName = deployment.metadata.name;
export const serviceName = service.metadata.name;
export const ingressHostname = ingress.spec.rules[0].host;
```

### Pulumi Configuration

```yaml
# file: pulumi/Pulumi.yaml
# version: 1.0.0
# guid: pulumi-project

name: ubuntu-autoinstall-agent
runtime: nodejs
description: Ubuntu Autoinstall Agent Infrastructure

config:
  kubernetes:kubeconfig:
    default: ~/.kube/config
```

```yaml
# file: pulumi/Pulumi.production.yaml
# version: 1.0.0
# guid: pulumi-stack-production

config:
  ubuntu-autoinstall-agent:namespace: ubuntu-autoinstall-production
  ubuntu-autoinstall-agent:appVersion: v1.0.0
  ubuntu-autoinstall-agent:replicaCount: 5
  ubuntu-autoinstall-agent:ingressHost: ubuntu-autoinstall.example.com
  ubuntu-autoinstall-agent:databaseUrl:
    secure: AAABAMfVNXXXXXXXXXXXXXXXXXXXXXX  # Encrypted
```

---

**Part 5 Complete**: Infrastructure as Code with Terraform (providers, variables, Kubernetes deployment
module with namespace/configmap/secret/deployment/service/ingress/HPA, Helm release integration) and
Pulumi TypeScript program (complete Kubernetes resources with type safety, stack-based configuration,
encrypted secrets). ✅

**Continue to Part 6** for deployment best practices, rollback strategies, and completion checklist.
