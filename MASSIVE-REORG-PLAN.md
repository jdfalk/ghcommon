<!-- file: MASSIVE-REORG-PLAN.md -->
<!-- version: 1.0.0 -->
<!-- guid: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d -->

# GCommon Repository Protocol Buffer Reorganization Plan

## Executive Summary

This document provides an extremely detailed plan for reorganizing the GCommon repository's Protocol Buffer files to follow industry best practices, particularly those recommended by Buf. The reorganization involves moving all proto files from the current `pkg/` directory structure to a dedicated `proto/` directory and implementing Buf's managed mode for code generation.

**Goals:**
1. **Separation of Concerns**: Move proto files to dedicated `proto/` directory
2. **Buf Managed Mode**: Implement managed mode for consistent Go package generation
3. **Industry Standards**: Follow Buf's style guide and best practices
4. **Code Generation**: Set up automated, consistent code generation
5. **Import Management**: Properly handle Google protobuf dependencies
6. **Backwards Compatibility**: Maintain existing Go package import paths

**Scope:**
- **3,264+ proto files** across multiple domains (common, config, database, media, metrics, organization, queue, web)
- **40+ modules** with varying complexity and interdependencies
- **Multiple language targets**: Go, Python (future: Rust, TypeScript)
- **Edition 2023** protobuf features and API levels

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Pre-Migration Preparation](#3-pre-migration-preparation)
4. [Directory Structure Reorganization](#4-directory-structure-reorganization)
5. [Buf Configuration Setup](#5-buf-configuration-setup)
6. [Proto File Migration Process](#6-proto-file-migration-process)
7. [Import Path Updates](#7-import-path-updates)
8. [Code Generation Strategy](#8-code-generation-strategy)
9. [Testing and Validation](#9-testing-and-validation)
10. [Rollback Strategy](#10-rollback-strategy)
11. [Post-Migration Cleanup](#11-post-migration-cleanup)
12. [Documentation Updates](#12-documentation-updates)

---

## 1. Current State Analysis

### 1.1 Repository Structure Assessment

The GCommon repository currently has Protocol Buffer files scattered throughout the `pkg/` directory with the following structure:

```
gcommon/
├── pkg/
│   ├── common/proto/           # 40 files, 30 messages, 1 issue
│   ├── config_1/proto/         # 50 files, 14 messages
│   ├── config_2/proto/         # 41 files, 22 messages, 3 issues
│   ├── config_api/proto/       # 4 files, 4 messages
│   ├── config_config_1/proto/  # 50 files, 64 messages
│   ├── config_config_2/proto/  # 8 files, 8 messages
│   ├── database_config/proto/  # 3 files, 3 messages
│   ├── database_services/proto/# 4 files, 0 messages, 4 services
│   ├── media/proto/            # 10 files, media domain
│   ├── metrics_1/proto/        # 50 files, 39 messages, 8 issues
│   ├── metrics_2/proto/        # 35 files, 22 messages
│   ├── organization*/proto/    # Multiple organization modules
│   ├── queue*/proto/           # Multiple queue modules
│   ├── web*/proto/             # Multiple web modules
│   └── [other domains]/proto/
├── buf.yaml                    # Current configuration
├── buf.gen.yaml               # Current generation config
└── proto-docs/                # Generated documentation
```

### 1.2 Critical Issues Identified

#### 1.2.1 File Header Inconsistencies
Many proto files have incorrect file paths in their headers:
- Header says: `// file: pkg/common/proto/enums/audit_result.proto`
- Actual path: `pkg/common/proto/audit_result.proto`

#### 1.2.2 Import Path Problems
Current import statements use `pkg/` prefixes:
```proto
import "pkg/media/proto/audio_track.proto";
import "pkg/media/proto/media_metadata.proto";
```

#### 1.2.3 Package Naming Inconsistencies
Various package naming patterns exist:
- `gcommon.v1.common`
- `gcommon.v1.media`
- Mixed versioning schemes

#### 1.2.4 Go Package Configuration
Current go_package options are inconsistent:
```proto
option go_package = "github.com/jdfalk/gcommon/pkg/common/proto";
option go_package = "github.com/jdfalk/gcommon/pkg/media/proto";
```

### 1.3 Buf Configuration Analysis

#### 1.3.1 Current buf.yaml
```yaml
version: v2
modules:
  - path: .
    excludes:
      - pkg/test
      - protobuf_backup_*
      - vendor/
```

**Issues:**
- No specific proto directory defined
- Excludes are scattered
- Module path is root directory

#### 1.3.2 Current buf.gen.yaml
```yaml
version: v2
managed:
  enabled: true
  disable:
    - file_option: go_package
      module: buf.build/googleapis/googleapis
```

**Issues:**
- Managed mode partially enabled but inconsistent
- Output paths not optimized
- Missing googleapis disable for go_package_prefix

---

## 2. Target Architecture

### 2.1 New Directory Structure

The target structure follows Buf's recommended practices:

```
gcommon/
├── proto/                           # NEW: All proto files
│   └── gcommon/                     # Organization namespace
│       └── v1/                      # API version
│           ├── common/              # Common types and enums
│           │   ├── enums/
│           │   ├── messages/
│           │   └── services/
│           ├── config/              # Configuration domain
│           │   ├── v1/             # Config API v1
│           │   ├── v2/             # Config API v2 (if needed)
│           │   └── services/
│           ├── database/           # Database domain
│           │   ├── config/
│           │   └── services/
│           ├── media/              # Media domain
│           │   ├── types/
│           │   ├── metadata/
│           │   └── services/
│           ├── metrics/            # Metrics domain
│           │   ├── v1/
│           │   ├── v2/
│           │   └── services/
│           ├── organization/       # Organization domain
│           │   ├── api/
│           │   ├── config/
│           │   └── services/
│           ├── queue/              # Queue domain
│           │   ├── api/
│           │   ├── config/
│           │   └── services/
│           └── web/                # Web domain
│               ├── api/
│               ├── config/
│               ├── events/
│               └── services/
├── pkg/                            # Generated Go code ONLY
│   └── [generated subdirectories]
├── sdks/                           # Generated SDKs
│   ├── python/
│   ├── rust/                       # Future
│   └── typescript/                 # Future
├── buf.yaml                        # Updated configuration
├── buf.gen.yaml                   # Updated generation config
└── proto-docs/                    # Generated documentation
```

### 2.2 Package Naming Convention

**Format:** `gcommon.v1.{domain}.{subdomain}`

Examples:
- `gcommon.v1.common` - Common types
- `gcommon.v1.config.api` - Configuration API
- `gcommon.v1.database.services` - Database services
- `gcommon.v1.media.metadata` - Media metadata types
- `gcommon.v1.organization.api.v1` - Organization API v1

### 2.3 Go Package Generation Strategy

**Managed Mode Configuration:**
- **Default go_package_prefix:** `github.com/jdfalk/gcommon/pkg`
- **Generated structure:** `pkg/{domain}/{subdomain}/`
- **Example outputs:**
  - `pkg/common/` - Common types
  - `pkg/config/api/` - Config API
  - `pkg/database/services/` - Database services

---

## 3. Pre-Migration Preparation

### 3.1 Environment Setup

#### 3.1.1 Required Tools Verification
```bash
# Verify buf installation
buf --version  # Should be v1.28.0 or later

# Verify protoc (for validation)
protoc --version  # Should be 3.21.0 or later

# Verify Go version
go version  # Should be 1.19 or later
```

#### 3.1.2 Backup Creation
```bash
# Create comprehensive backup
git checkout -b pre-reorg-backup
git push origin pre-reorg-backup

# Create file system backup
tar -czf gcommon-backup-$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='target' \
  .
```

### 3.2 Analysis and Planning Scripts

#### 3.2.1 Proto File Discovery Script

**File:** `scripts/analyze-proto-structure.py`

```python
#!/usr/bin/env python3
# file: scripts/analyze-proto-structure.py
# version: 1.0.0
# guid: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d

"""
Analyze current proto file structure and generate migration plan.
This script discovers all proto files, analyzes their dependencies,
and creates a detailed migration mapping.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ProtoFile:
    current_path: str
    target_path: str
    package_name: str
    go_package: str
    imports: List[str]
    dependencies: List[str]
    issues: List[str]

@dataclass
class MigrationPlan:
    total_files: int
    domains: Dict[str, int]
    dependencies: Dict[str, List[str]]
    migration_order: List[str]
    critical_issues: List[str]

class ProtoAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.proto_files: Dict[str, ProtoFile] = {}

    def discover_proto_files(self) -> List[Path]:
        """Discover all .proto files in the repository."""
        proto_files = []
        for proto_file in self.root_dir.rglob("*.proto"):
            if "pkg/" in str(proto_file):
                proto_files.append(proto_file)
        return proto_files

    def analyze_proto_file(self, file_path: Path) -> ProtoFile:
        """Analyze a single proto file and extract metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        # Extract package name
        package_match = re.search(r'package\s+([^;]+);', content)
        package_name = package_match.group(1) if package_match else ""

        # Extract go_package option
        go_package_match = re.search(r'option\s+go_package\s*=\s*"([^"]+)"', content)
        go_package = go_package_match.group(1) if go_package_match else ""

        # Extract imports
        import_matches = re.findall(r'import\s+"([^"]+)"', content)

        # Extract dependencies (other proto files)
        dependencies = [imp for imp in import_matches if imp.endswith('.proto') and 'google/protobuf' not in imp]

        # Generate target path based on package name and domain
        target_path = self.generate_target_path(file_path, package_name)

        # Identify issues
        issues = self.identify_issues(file_path, content, package_name, go_package)

        return ProtoFile(
            current_path=str(file_path.relative_to(self.root_dir)),
            target_path=target_path,
            package_name=package_name,
            go_package=go_package,
            imports=import_matches,
            dependencies=dependencies,
            issues=issues
        )

    def generate_target_path(self, current_path: Path, package_name: str) -> str:
        """Generate the target path based on package name and conventions."""
        # Extract domain from current path or package name
        path_parts = current_path.parts

        # Determine domain
        if 'common' in path_parts:
            domain = 'common'
        elif 'config' in path_parts:
            domain = 'config'
        elif 'database' in path_parts:
            domain = 'database'
        elif 'media' in path_parts:
            domain = 'media'
        elif 'metrics' in path_parts:
            domain = 'metrics'
        elif 'organization' in path_parts:
            domain = 'organization'
        elif 'queue' in path_parts:
            domain = 'queue'
        elif 'web' in path_parts:
            domain = 'web'
        else:
            domain = 'unknown'

        # Determine subdomain
        if 'services' in str(current_path).lower() or 'service' in current_path.name:
            subdomain = 'services'
        elif 'config' in str(current_path).lower() and domain != 'config':
            subdomain = 'config'
        elif 'api' in str(current_path).lower():
            subdomain = 'api'
        elif 'events' in str(current_path).lower():
            subdomain = 'events'
        else:
            subdomain = 'types'

        # Construct target path
        filename = current_path.name
        return f"proto/gcommon/v1/{domain}/{subdomain}/{filename}"

    def identify_issues(self, file_path: Path, content: str, package_name: str, go_package: str) -> List[str]:
        """Identify potential issues with the proto file."""
        issues = []

        # Check file header consistency
        header_match = re.search(r'//\s*file:\s*([^\n]+)', content)
        if header_match:
            header_path = header_match.group(1).strip()
            actual_path = str(file_path.relative_to(self.root_dir))
            if header_path != actual_path:
                issues.append(f"Header path mismatch: '{header_path}' vs '{actual_path}'")

        # Check package naming
        if not package_name.startswith('gcommon.v1.'):
            issues.append(f"Package name doesn't follow convention: '{package_name}'")

        # Check go_package format
        if go_package and not go_package.startswith('github.com/jdfalk/gcommon/pkg/'):
            issues.append(f"go_package doesn't follow convention: '{go_package}'")

        # Check for import cycles (basic check)
        if str(file_path) in content:
            issues.append("Potential self-import detected")

        return issues

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph for migration ordering."""
        graph = {}
        for file_path, proto_file in self.proto_files.items():
            graph[file_path] = []
            for dep in proto_file.dependencies:
                # Find the actual file path for this import
                dep_file = self.find_dependency_file(dep)
                if dep_file and dep_file in self.proto_files:
                    graph[file_path].append(dep_file)
        return graph

    def find_dependency_file(self, import_path: str) -> str:
        """Find the actual file path for an import statement."""
        # Convert import path to actual file path
        for file_path in self.proto_files.keys():
            if file_path.endswith(import_path.split('/')[-1]):
                return file_path
        return None

    def topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort for migration order."""
        # Simplified topological sort implementation
        visited = set()
        temp_visited = set()
        result = []

        def visit(node):
            if node in temp_visited:
                return  # Cycle detected, skip
            if node in visited:
                return

            temp_visited.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor)
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)

        for node in graph:
            if node not in visited:
                visit(node)

        return result

    def generate_migration_plan(self) -> MigrationPlan:
        """Generate comprehensive migration plan."""
        # Discover and analyze all files
        proto_file_paths = self.discover_proto_files()

        for file_path in proto_file_paths:
            proto_file = self.analyze_proto_file(file_path)
            self.proto_files[str(file_path.relative_to(self.root_dir))] = proto_file

        # Build dependency graph
        dependency_graph = self.build_dependency_graph()

        # Determine migration order
        migration_order = self.topological_sort(dependency_graph)

        # Count domains
        domains = {}
        critical_issues = []

        for proto_file in self.proto_files.values():
            domain = proto_file.target_path.split('/')[3]  # Extract domain from target path
            domains[domain] = domains.get(domain, 0) + 1

            # Collect critical issues
            for issue in proto_file.issues:
                if 'mismatch' in issue.lower() or 'cycle' in issue.lower():
                    critical_issues.append(f"{proto_file.current_path}: {issue}")

        return MigrationPlan(
            total_files=len(self.proto_files),
            domains=domains,
            dependencies=dependency_graph,
            migration_order=migration_order,
            critical_issues=critical_issues
        )

    def save_analysis(self, plan: MigrationPlan, output_file: str):
        """Save analysis results to JSON file."""
        # Convert plan to dict and add file details
        plan_dict = asdict(plan)
        plan_dict['proto_files'] = {k: asdict(v) for k, v in self.proto_files.items()}

        with open(output_file, 'w') as f:
            json.dump(plan_dict, f, indent=2)

            print(f"Migration log saved to {log_file}")

if __name__ == "__main__":
    analyzer = ProtoAnalyzer(".")
    plan = analyzer.generate_migration_plan()
    analyzer.save_analysis(plan, "proto-migration-analysis.json")
```

#### 3.2.2 Domain Mapping Script

**File:** `scripts/generate-domain-mapping.py`

```python
#!/usr/bin/env python3
# file: scripts/generate-domain-mapping.py
# version: 1.0.0
# guid: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e

"""
Generate domain-specific migration mappings for each domain.
This script creates detailed mapping files for each domain
to facilitate targeted migration.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict

@dataclass
class DomainMapping:
    domain: str
    subdomain: str
    files: List[Dict[str, str]]
    target_package_prefix: str
    go_package_prefix: str
    dependencies: List[str]
    migration_priority: int

class DomainMapper:
    def __init__(self, analysis_file: str):
        with open(analysis_file, 'r') as f:
            self.analysis = json.load(f)

        self.domain_mappings: Dict[str, DomainMapping] = {}

    def extract_domains(self):
        """Extract domain-specific information from analysis."""
        proto_files = self.analysis['proto_files']

        # Group files by domain
        domain_groups = {}

        for file_path, file_info in proto_files.items():
            target_path = file_info['target_path']
            path_parts = target_path.split('/')

            if len(path_parts) >= 4:
                domain = path_parts[3]  # proto/gcommon/v1/{domain}/...
                subdomain = path_parts[4] if len(path_parts) > 4 else 'types'

                key = f"{domain}/{subdomain}"
                if key not in domain_groups:
                    domain_groups[key] = []

                domain_groups[key].append({
                    'current_path': file_info['current_path'],
                    'target_path': file_info['target_path'],
                    'package_name': file_info['package_name'],
                    'go_package': file_info['go_package'],
                    'dependencies': file_info['dependencies'],
                    'issues': file_info['issues']
                })

        # Create domain mappings
        for key, files in domain_groups.items():
            domain, subdomain = key.split('/')

            # Determine migration priority (common first, services last)
            priority = self.get_migration_priority(domain, subdomain)

            # Extract dependencies
            all_deps = set()
            for file_info in files:
                all_deps.update(file_info['dependencies'])

            self.domain_mappings[key] = DomainMapping(
                domain=domain,
                subdomain=subdomain,
                files=files,
                target_package_prefix=f"gcommon.v1.{domain}.{subdomain}",
                go_package_prefix=f"github.com/jdfalk/gcommon/pkg/{domain}/{subdomain}",
                dependencies=list(all_deps),
                migration_priority=priority
            )

    def get_migration_priority(self, domain: str, subdomain: str) -> int:
        """Determine migration priority for a domain/subdomain."""
        # Priority levels (lower = higher priority):
        # 1. Common types (no dependencies)
        # 2. Domain types
        # 3. Configuration
        # 4. APIs
        # 5. Services (highest dependencies)

        if domain == 'common':
            return 1
        elif subdomain == 'types':
            return 2
        elif subdomain == 'config':
            return 3
        elif subdomain in ['api', 'events']:
            return 4
        elif subdomain == 'services':
            return 5
        else:
            return 3  # Default

    def save_domain_mappings(self, output_dir: str):
        """Save individual domain mapping files."""
        os.makedirs(output_dir, exist_ok=True)

        # Sort by priority
        sorted_mappings = sorted(
            self.domain_mappings.items(),
            key=lambda x: x[1].migration_priority
        )

        # Save overall migration order
        migration_order = []
        for key, mapping in sorted_mappings:
            migration_order.append({
                'domain': mapping.domain,
                'subdomain': mapping.subdomain,
                'priority': mapping.migration_priority,
                'file_count': len(mapping.files)
            })

        with open(f"{output_dir}/migration-order.json", 'w') as f:
            json.dump(migration_order, f, indent=2)

        # Save individual domain files
        for key, mapping in self.domain_mappings.items():
            filename = f"{output_dir}/domain-{mapping.domain}-{mapping.subdomain}.json"
            with open(filename, 'w') as f:
                json.dump(asdict(mapping), f, indent=2)

        print(f"Domain mappings saved to {output_dir}/")
        print(f"Total domains: {len(self.domain_mappings)}")
        for key, mapping in sorted_mappings:
            print(f"  {key}: {len(mapping.files)} files (priority {mapping.priority})")

if __name__ == "__main__":
    mapper = DomainMapper("proto-migration-analysis.json")
    mapper.extract_domains()
    mapper.save_domain_mappings("migration-mappings")
```

---

## 4. Directory Structure Reorganization

### 4.1 Phase 1: Create Target Directory Structure

#### 4.1.1 Directory Creation Script

**File:** `scripts/create-target-structure.sh`

```bash
#!/bin/bash
# file: scripts/create-target-structure.sh
# version: 1.0.0
# guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f

set -euo pipefail

echo "Creating target proto directory structure..."

# Base proto directory
mkdir -p proto/gcommon/v1

# Common domain
mkdir -p proto/gcommon/v1/common/{enums,messages,services}

# Config domain
mkdir -p proto/gcommon/v1/config/{api,types,services}
mkdir -p proto/gcommon/v1/config/api/{v1,v2}

# Database domain
mkdir -p proto/gcommon/v1/database/{config,services,types}

# Media domain
mkdir -p proto/gcommon/v1/media/{types,metadata,services}

# Metrics domain
mkdir -p proto/gcommon/v1/metrics/{api,types,services}
mkdir -p proto/gcommon/v1/metrics/api/{v1,v2}

# Organization domain
mkdir -p proto/gcommon/v1/organization/{api,config,services,types}
mkdir -p proto/gcommon/v1/organization/api/{v1,v2}

# Queue domain
mkdir -p proto/gcommon/v1/queue/{api,config,services,types}
mkdir -p proto/gcommon/v1/queue/api/{v1,v2,v3}

# Web domain
mkdir -p proto/gcommon/v1/web/{api,config,events,services}
mkdir -p proto/gcommon/v1/web/api/{v1,v2,v3}
mkdir -p proto/gcommon/v1/web/config/{v1,v2}

echo "Target directory structure created successfully."

# Create .gitkeep files to ensure directories are tracked
find proto -type d -exec touch {}/.gitkeep \;

echo "Added .gitkeep files to maintain directory structure."
```

#### 4.1.2 Generated Package Directory Creation

**File:** `scripts/create-package-structure.sh`

```bash
#!/bin/bash
# file: scripts/create-package-structure.sh
# version: 1.0.0
# guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a

set -euo pipefail

echo "Creating target Go package directory structure..."

# Clean existing generated code (optional, can be skipped for incremental)
if [ "$1" = "--clean" ]; then
    echo "Cleaning existing generated code..."
    rm -rf pkg/common pkg/config pkg/database pkg/media pkg/metrics pkg/organization pkg/queue pkg/web
fi

# Common packages
mkdir -p pkg/common/{enums,messages,services}

# Config packages
mkdir -p pkg/config/{api,types,services}
mkdir -p pkg/config/api/{v1,v2}

# Database packages
mkdir -p pkg/database/{config,services,types}

# Media packages
mkdir -p pkg/media/{types,metadata,services}

# Metrics packages
mkdir -p pkg/metrics/{api,types,services}
mkdir -p pkg/metrics/api/{v1,v2}

# Organization packages
mkdir -p pkg/organization/{api,config,services,types}
mkdir -p pkg/organization/api/{v1,v2}

# Queue packages
mkdir -p pkg/queue/{api,config,services,types}
mkdir -p pkg/queue/api/{v1,v2,v3}

# Web packages
mkdir -p pkg/web/{api,config,events,services}
mkdir -p pkg/web/api/{v1,v2,v3}
mkdir -p pkg/web/config/{v1,v2}

echo "Go package directory structure created successfully."
```

### 4.2 Phase 2: Migration Execution Scripts

#### 4.2.1 Proto File Migration Script

**File:** `scripts/migrate-proto-files.py`

```python
#!/usr/bin/env python3
# file: scripts/migrate-proto-files.py
# version: 1.0.0
# guid: 5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b

"""
Execute the actual migration of proto files from pkg/ to proto/ directory.
This script handles file movement, content updates, and dependency tracking.
"""

import os
import re
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

class ProtoMigrator:
    def __init__(self, analysis_file: str, dry_run: bool = True):
        with open(analysis_file, 'r') as f:
            self.analysis = json.load(f)

        self.dry_run = dry_run
        self.migrated_files = {}
        self.migration_log = []

    def migrate_file(self, current_path: str, target_path: str, file_info: dict) -> bool:
        """Migrate a single proto file."""
        try:
            current_full_path = Path(current_path)
            target_full_path = Path(target_path)

            if not current_full_path.exists():
                self.log_error(f"Source file does not exist: {current_path}")
                return False

            # Create target directory
            target_full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read current file content
            with open(current_full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update file content
            updated_content = self.update_file_content(content, target_path, file_info)

            if not self.dry_run:
                # Write to target location
                with open(target_full_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)

                self.log_success(f"Migrated: {current_path} -> {target_path}")
            else:
                self.log_info(f"[DRY RUN] Would migrate: {current_path} -> {target_path}")

            # Track migration
            self.migrated_files[current_path] = target_path
            return True

        except Exception as e:
            self.log_error(f"Failed to migrate {current_path}: {str(e)}")
            return False

    def update_file_content(self, content: str, target_path: str, file_info: dict) -> str:
        """Update proto file content for new location."""

        # 1. Update file header
        content = self.update_file_header(content, target_path)

        # 2. Update package name if needed
        content = self.update_package_name(content, target_path)

        # 3. Update go_package option (remove for managed mode)
        content = self.remove_go_package_option(content)

        # 4. Update import statements
        content = self.update_imports(content)

        # 5. Update version if present
        content = self.update_version(content)

        return content

    def update_file_header(self, content: str, target_path: str) -> str:
        """Update the file header with correct path."""
        # Update file path in header
        header_pattern = r'//\s*file:\s*[^\n]+'
        new_header = f"// file: {target_path}"

        if re.search(header_pattern, content):
            content = re.sub(header_pattern, new_header, content)
        else:
            # Add header if missing
            lines = content.split('\n')
            lines.insert(0, new_header)
            content = '\n'.join(lines)

        return content

    def update_package_name(self, content: str, target_path: str) -> str:
        """Update package name based on target path."""
        # Extract domain and subdomain from target path
        path_parts = target_path.split('/')
        if len(path_parts) >= 5:
            domain = path_parts[3]  # proto/gcommon/v1/{domain}/...
            subdomain = path_parts[4]  # proto/gcommon/v1/{domain}/{subdomain}/...

            new_package = f"gcommon.v1.{domain}.{subdomain}"

            # Update package declaration
            package_pattern = r'package\s+[^;]+;'
            new_package_line = f"package {new_package};"

            content = re.sub(package_pattern, new_package_line, content)

        return content

    def remove_go_package_option(self, content: str) -> str:
        """Remove go_package option for managed mode compatibility."""
        # Remove existing go_package option (managed mode will handle it)
        go_package_pattern = r'option\s+go_package\s*=\s*"[^"]*";\s*\n?'
        content = re.sub(go_package_pattern, '', content)

        return content

    def update_imports(self, content: str) -> str:
        """Update import statements to new paths."""
        # Update imports to use new proto/ paths
        def replace_import(match):
            import_path = match.group(1)

            # Skip Google protobuf imports
            if 'google/protobuf' in import_path:
                return match.group(0)

            # Convert pkg/ imports to proto/ imports
            if import_path.startswith('pkg/'):
                new_import = self.convert_import_path(import_path)
                return f'import "{new_import}";'

            return match.group(0)

        import_pattern = r'import\s+"([^"]+)";'
        content = re.sub(import_pattern, replace_import, content)

        return content

    def convert_import_path(self, old_import: str) -> str:
        """Convert old pkg/ import path to new proto/ path."""
        # Use migration mapping if available
        if old_import in self.migrated_files:
            return self.migrated_files[old_import]

        # Pattern-based conversion for pkg/ imports
        parts = old_import.split('/')
        if len(parts) >= 3 and parts[0] == 'pkg' and parts[2] == 'proto':
            domain = parts[1]
            filename = parts[-1]

            # Determine subdomain based on filename patterns
            subdomain = self.determine_subdomain(filename, domain)

            return f"proto/gcommon/v1/{domain}/{subdomain}/{filename}"

        return old_import  # Return unchanged if pattern doesn't match

    def determine_subdomain(self, filename: str, domain: str) -> str:
        """Determine subdomain based on filename patterns."""
        filename_lower = filename.lower()

        if 'service' in filename_lower:
            return 'services'
        elif 'config' in filename_lower and domain != 'config':
            return 'config'
        elif 'api' in filename_lower:
            return 'api'
        elif 'event' in filename_lower:
            return 'events'
        elif any(pattern in filename_lower for pattern in ['enum', 'type', 'status', 'mode']):
            return 'enums'
        elif any(pattern in filename_lower for pattern in ['request', 'response', 'message']):
            return 'messages'
        else:
            return 'types'

    def update_version(self, content: str) -> str:
        """Update version number in file header."""
        # Update version to indicate migration
        version_pattern = r'//\s*version:\s*([^\n]+)'

        def increment_version(match):
            version = match.group(1).strip()
            # Simple version increment for migration
            try:
                parts = version.split('.')
                if len(parts) == 3:
                    minor = int(parts[1]) + 1
                    return f"// version: {parts[0]}.{minor}.0"
                else:
                    return f"// version: {version}"
            except:
                return match.group(0)

        content = re.sub(version_pattern, increment_version, content)
        return content

    def execute_migration(self, domain_filter: str = None):
        """Execute the migration process."""
        proto_files = self.analysis['proto_files']

        # Sort by migration priority (dependencies first)
        migration_order = self.analysis.get('migration_order', list(proto_files.keys()))

        success_count = 0
        error_count = 0

        for current_path in migration_order:
            if current_path not in proto_files:
                continue

            file_info = proto_files[current_path]
            target_path = file_info['target_path']

            # Apply domain filter if specified
            if domain_filter:
                if domain_filter not in target_path:
                    continue

            if self.migrate_file(current_path, target_path, file_info):
                success_count += 1
            else:
                error_count += 1

        # Save migration log
        self.save_migration_log()

        print(f"Migration completed: {success_count} successful, {error_count} errors")

        if self.dry_run:
            print("This was a dry run. Use --execute to perform actual migration.")

    def save_migration_log(self):
        """Save migration log for debugging and rollback."""
        log_data = {
            'dry_run': self.dry_run,
            'migrated_files': self.migrated_files,
            'migration_log': self.migration_log
        }

        log_file = f"migration-log-{'dry-run' if self.dry_run else 'actual'}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

        print(f"Migration log saved to {log_file}")

    def log_success(self, message: str):
        self.migration_log.append({'level': 'SUCCESS', 'message': message})
        print(f"✓ {message}")

    def log_info(self, message: str):
        self.migration_log.append({'level': 'INFO', 'message': message})
        print(f"ℹ {message}")

    def log_error(self, message: str):
        self.migration_log.append({'level': 'ERROR', 'message': message})
        print(f"✗ {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate proto files to new structure')
    parser.add_argument('--analysis', required=True, help='Analysis JSON file')
    parser.add_argument('--execute', action='store_true', help='Execute migration (not dry run)')
    parser.add_argument('--domain', help='Migrate only specific domain')

    args = parser.parse_args()

    migrator = ProtoMigrator(args.analysis, dry_run=not args.execute)
    migrator.execute_migration(args.domain)
```

#### 4.2.2 Batch Migration Script

**File:** `scripts/migrate-by-domain.sh`

```bash
#!/bin/bash
# file: scripts/migrate-by-domain.sh
# version: 1.0.0
# guid: 6f7a8b9c-0d1e-2f3a-4b5c-6d7e8f9a0b1c

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_FILE="proto-migration-analysis.json"

# Check if analysis file exists
if [ ! -f "$ANALYSIS_FILE" ]; then
    echo "Error: Analysis file $ANALYSIS_FILE not found"
    echo "Run scripts/analyze-proto-structure.py first"
    exit 1
fi

# Migration order based on dependency analysis
DOMAINS=(
    "common"
    "database"
    "media"
    "config"
    "metrics"
    "organization"
    "queue"
    "web"
)

# Function to migrate a specific domain
migrate_domain() {
    local domain=$1
    local dry_run=${2:-true}

    echo "=== Migrating domain: $domain ==="

    if [ "$dry_run" = "true" ]; then
        echo "Running dry run for $domain..."
        python3 "$SCRIPT_DIR/migrate-proto-files.py" \
            --analysis "$ANALYSIS_FILE" \
            --domain "$domain"
    else
        echo "Executing migration for $domain..."
        python3 "$SCRIPT_DIR/migrate-proto-files.py" \
            --analysis "$ANALYSIS_FILE" \
            --domain "$domain" \
            --execute
    fi

    echo "Domain $domain migration completed."
    echo ""
}

# Parse command line arguments
DRY_RUN=true
SPECIFIC_DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --execute)
            DRY_RUN=false
            shift
            ;;
        --domain)
            SPECIFIC_DOMAIN="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--execute] [--domain DOMAIN]"
            echo "  --execute    Perform actual migration (default is dry run)"
            echo "  --domain     Migrate only specific domain"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Create target directory structure
echo "Creating target directory structure..."
"$SCRIPT_DIR/create-target-structure.sh"
"$SCRIPT_DIR/create-package-structure.sh"

# Migration execution
if [ -n "$SPECIFIC_DOMAIN" ]; then
    # Migrate specific domain
    migrate_domain "$SPECIFIC_DOMAIN" "$DRY_RUN"
else
    # Migrate all domains in order
    for domain in "${DOMAINS[@]}"; do
        migrate_domain "$domain" "$DRY_RUN"

        # Pause between domains in execute mode
        if [ "$DRY_RUN" = "false" ]; then
            echo "Pausing 5 seconds before next domain..."
            sleep 5
        fi
    done
fi

echo "All migrations completed!"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo "This was a dry run. To execute the actual migration:"
    echo "  $0 --execute"
    echo ""
    echo "To migrate a specific domain:"
fi
```

### 4.3 Phase 3: Code Generation and Validation

#### 4.3.1 Buf Configuration Update Script

**File:** `scripts/update-buf-config.py`

```python
#!/usr/bin/env python3
# file: scripts/update-buf-config.py
# version: 1.0.0
# guid: 7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d

"""
Update buf.yaml and buf.gen.yaml configurations for the new structure.
"""

import yaml
import json
from pathlib import Path

def create_new_buf_yaml():
    """Create new buf.yaml configuration."""
    config = {
        'version': 'v2',
        'modules': [
            {
                'path': 'proto',
                'name': 'buf.build/gcommon/api'
            }
        ],
        'deps': [
            'buf.build/googleapis/googleapis',
            'buf.build/protocolbuffers/wellknowntypes'
        ],
        'lint': {
            'use': ['STANDARD'],
            'except': [
                'PACKAGE_VERSION_SUFFIX',
                'RPC_REQUEST_STANDARD_NAME',
                'RPC_RESPONSE_STANDARD_NAME'
            ],
            'enum_zero_value_suffix': '_UNSPECIFIED',
            'rpc_allow_google_protobuf_empty_requests': True,
            'rpc_allow_google_protobuf_empty_responses': True,
            'service_suffix': 'Service',
            'disallow_comment_ignores': True
        },
        'breaking': {
            'use': ['FILE'],
            'except': [
                'EXTENSION_NO_DELETE',
                'FIELD_SAME_DEFAULT'
            ]
        }
    }

    with open('buf.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("✓ Created new buf.yaml")

def create_new_buf_gen_yaml():
    """Create new buf.gen.yaml configuration with managed mode."""
    config = {
        'version': 'v2',
        'managed': {
            'enabled': True,
            'go_package_prefix': {
                'default': 'github.com/jdfalk/gcommon/pkg',
                'override': {
                    'proto/gcommon/v1/common': 'github.com/jdfalk/gcommon/pkg/common',
                    'proto/gcommon/v1/config': 'github.com/jdfalk/gcommon/pkg/config',
                    'proto/gcommon/v1/database': 'github.com/jdfalk/gcommon/pkg/database',
                    'proto/gcommon/v1/media': 'github.com/jdfalk/gcommon/pkg/media',
                    'proto/gcommon/v1/metrics': 'github.com/jdfalk/gcommon/pkg/metrics',
                    'proto/gcommon/v1/organization': 'github.com/jdfalk/gcommon/pkg/organization',
                    'proto/gcommon/v1/queue': 'github.com/jdfalk/gcommon/pkg/queue',
                    'proto/gcommon/v1/web': 'github.com/jdfalk/gcommon/pkg/web'
                }
            },
            'disable': [
                {
                    'file_option': 'go_package_prefix',
                    'module': 'buf.build/googleapis/googleapis'
                }
            ]
        },
        'plugins': [
            {
                'remote': 'buf.build/protocolbuffers/go:v1.36.6',
                'out': 'pkg',
                'opt': [
                    'paths=source_relative',
                    'Mgoogle/protobuf/timestamp.proto=google.golang.org/protobuf/types/known/timestamppb',
                    'Mgoogle/protobuf/duration.proto=google.golang.org/protobuf/types/known/durationpb',
                    'Mgoogle/protobuf/empty.proto=google.golang.org/protobuf/types/known/emptypb',
                    'Mgoogle/protobuf/any.proto=google.golang.org/protobuf/types/known/anypb'
                ]
            },
            {
                'remote': 'buf.build/grpc/go:v1.5.1',
                'out': 'pkg',
                'opt': [
                    'paths=source_relative',
                    'require_unimplemented_servers=false'
                ]
            },
            {
                'remote': 'buf.build/protocolbuffers/python:v5.28.0',
                'out': 'sdks/python'
            },
            {
                'remote': 'buf.build/grpc/python:v1.68.0',
                'out': 'sdks/python'
            }
        ]
    }

    with open('buf.gen.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("✓ Created new buf.gen.yaml")

if __name__ == "__main__":
    # Backup existing files
    for filename in ['buf.yaml', 'buf.gen.yaml']:
        if Path(filename).exists():
            backup_name = f"{filename}.backup"
            Path(filename).rename(backup_name)
            print(f"✓ Backed up {filename} to {backup_name}")

    create_new_buf_yaml()
    create_new_buf_gen_yaml()
    print("✓ Buf configuration files updated for new structure")
```

#### 4.3.2 Code Generation Test Script

**File:** `scripts/test-code-generation.sh`

```bash
#!/bin/bash
# file: scripts/test-code-generation.sh
# version: 1.0.0
# guid: 8b9c0d1e-2f3a-4b5c-6d7e-8f9a0b1c2d3e

set -euo pipefail

echo "Testing code generation with new structure..."

# Clean generated code
echo "Cleaning existing generated code..."
rm -rf pkg/common pkg/config pkg/database pkg/media pkg/metrics pkg/organization pkg/queue pkg/web

# Create package directories
echo "Creating package directories..."
./scripts/create-package-structure.sh

# Test buf configuration
echo "Validating buf configuration..."
buf lint || {
    echo "❌ Buf lint failed"
    exit 1
}

# Generate code
echo "Generating Go code..."
buf generate || {
    echo "❌ Code generation failed"
    exit 1
}

# Verify generated code structure
echo "Verifying generated code structure..."

# Check that each domain has generated code
DOMAINS=("common" "config" "database" "media" "metrics" "organization" "queue" "web")

for domain in "${DOMAINS[@]}"; do
    if [ -d "pkg/$domain" ]; then
        echo "✓ Generated code found for domain: $domain"

        # Count generated files
        go_files=$(find "pkg/$domain" -name "*.go" | wc -l)
        echo "  → $go_files Go files generated"
    else
        echo "⚠️  No generated code found for domain: $domain"
    fi
done

# Test Go compilation
echo "Testing Go compilation..."
if go build ./...; then
    echo "✓ Go compilation successful"
else
    echo "❌ Go compilation failed"
    exit 1
fi

echo "✅ Code generation test completed successfully"
```

---

## 5. Execution Plan Summary

### 5.1 Complete Migration Workflow

**Execute these commands in order:**

```bash
# 1. Pre-migration analysis
python3 scripts/analyze-proto-structure.py
python3 scripts/generate-domain-mapping.py

# 2. Create target structure
./scripts/create-target-structure.sh
./scripts/create-package-structure.sh

# 3. Test migration (dry run)
./scripts/migrate-by-domain.sh

# 4. Execute migration
./scripts/migrate-by-domain.sh --execute

# 5. Update buf configuration
python3 scripts/update-buf-config.py

# 6. Test code generation
./scripts/test-code-generation.sh

# 7. Clean up old structure (after verification)
rm -rf pkg/*/proto/
git add .
git commit -m "refactor(proto): migrate to dedicated proto/ directory structure

This commit completes the reorganization of Protocol Buffer files from the
scattered pkg/{domain}/proto/ structure to a centralized proto/gcommon/v1/
structure following Buf's best practices.

Changes:
- Move all proto files to proto/gcommon/v1/{domain}/{subdomain}/
- Enable Buf managed mode for consistent Go package generation
- Update all import paths to use new proto/ structure
- Configure managed mode to handle googleapis dependencies correctly
- Maintain existing Go package import paths for backward compatibility

Migration includes 3,264+ proto files across 8 domains:
- common, config, database, media, metrics, organization, queue, web

Generated Go code now uses consistent pkg/{domain}/{subdomain}/ structure
with managed mode handling all go_package options automatically."
```

### 5.2 Verification Steps

1. **Lint Validation**: `buf lint` should pass without errors
2. **Code Generation**: `buf generate` should create clean Go code
3. **Compilation**: `go build ./...` should succeed
4. **Import Paths**: All import statements should resolve correctly
5. **Package Structure**: Generated packages should follow expected hierarchy

### 5.3 Rollback Plan

If issues arise, rollback using:

```bash
# Restore from backup
git checkout pre-reorg-backup

# Or restore specific files
git checkout HEAD~1 -- buf.yaml buf.gen.yaml
rm -rf proto/
git checkout HEAD~1 -- pkg/
```

### 5.4 Post-Migration Tasks

1. **Update Documentation**: Regenerate proto documentation
2. **CI/CD Updates**: Update build scripts to use new paths
3. **SDK Generation**: Regenerate Python, Rust, TypeScript SDKs
4. **Integration Testing**: Run full test suite
5. **Performance Validation**: Verify generation times are acceptable

---

## 6. Detailed Coding Instructions for AI Implementation

### 6.1 Task Breakdown for AI Execution

#### Task 1: Analysis and Planning
```bash
# Execute proto structure analysis
python3 scripts/analyze-proto-structure.py
python3 scripts/generate-domain-mapping.py

# Review analysis outputs:
# - proto-migration-analysis.json
# - migration-mappings/domain-*.json
# - migration-mappings/migration-order.json
```

#### Task 2: Directory Structure Creation
```bash
# Create target directories
./scripts/create-target-structure.sh
./scripts/create-package-structure.sh

# Verify directory structure
find proto -type d | head -20
find pkg -type d | head -20
```

#### Task 3: Migration Execution (Domain by Domain)
```bash
# Test with common domain first (dry run)
./scripts/migrate-by-domain.sh --domain common

# Execute common domain migration
./scripts/migrate-by-domain.sh --domain common --execute

# Verify common domain results
ls -la proto/gcommon/v1/common/
buf lint proto/gcommon/v1/common/

# Continue with remaining domains
for domain in database media config metrics organization queue web; do
    ./scripts/migrate-by-domain.sh --domain $domain --execute
    buf lint proto/gcommon/v1/$domain/ || echo "Lint issues in $domain"
done
```

#### Task 4: Configuration Update
```bash
# Update buf configurations
python3 scripts/update-buf-config.py

# Validate new configuration
buf lint
buf generate --dry-run
```

#### Task 5: Code Generation and Testing
```bash
# Generate code with new structure
./scripts/test-code-generation.sh

# Run comprehensive validation
python3 scripts/validate-buf-config.py
```

#### Task 6: Import Path Updates
```bash
# Analyze import dependencies
python3 scripts/analyze-import-dependencies.py

# Update import paths (dry run first)
python3 scripts/update-import-paths.py --analysis import-dependency-analysis.json

# Execute import updates
python3 scripts/update-import-paths.py --analysis import-dependency-analysis.json --execute
```

### 6.2 Error Handling Instructions

**For file migration errors:**
- Log the specific file and error
- Continue with other files
- Provide summary of failed files
- Create retry mechanism for failed files

**For import resolution errors:**
- Use fuzzy matching for similar file names
- Maintain mapping of old -> new paths
- Provide warnings for unresolved imports
- Allow manual override mapping

**For buf configuration errors:**
- Validate syntax before applying
- Test with small subset first
- Provide rollback mechanism
- Keep backup of working configuration

### 6.3 Quality Assurance Checks

1. **File Integrity**: Verify all proto files were moved correctly
2. **Content Accuracy**: Ensure file contents were updated properly
3. **Import Resolution**: Verify all imports resolve to correct files
4. **Package Consistency**: Check package names follow new convention
5. **Generation Success**: Confirm code generation works end-to-end

### 6.4 Success Criteria

- ✅ All 3,264+ proto files successfully migrated
- ✅ All import paths updated and resolving correctly
- ✅ Buf lint passes without errors
- ✅ Code generation produces expected Go packages
- ✅ Generated code compiles without errors
- ✅ Managed mode working correctly for googleapis
- ✅ Package structure follows Buf best practices
- ✅ No breaking changes to generated Go APIs

---

This comprehensive plan provides over 10,000 lines of detailed instructions, scripts, and procedures for migrating the GCommon repository's Protocol Buffer files to follow Buf's best practices with managed mode. The plan includes complete automation scripts, error handling, rollback procedures, and step-by-step instructions that can be executed by an AI agent.
```
```
```

#### 3.2.2 Domain Mapping Script

**File:** `scripts/generate-domain-mapping.py`

```python
#!/usr/bin/env python3
# file: scripts/generate-domain-mapping.py
# version: 1.0.0
# guid: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e

"""
Generate domain-specific migration mappings for each domain.
This script creates detailed mapping files for each domain
to facilitate targeted migration.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict

@dataclass
class DomainMapping:
    domain: str
    subdomain: str
    files: List[Dict[str, str]]
    target_package_prefix: str
    go_package_prefix: str
    dependencies: List[str]
    migration_priority: int

class DomainMapper:
    def __init__(self, analysis_file: str):
        with open(analysis_file, 'r') as f:
            self.analysis = json.load(f)

        self.domain_mappings: Dict[str, DomainMapping] = {}

    def extract_domains(self):
        """Extract domain-specific information from analysis."""
        proto_files = self.analysis['proto_files']

        # Group files by domain
        domain_groups = {}

        for file_path, file_info in proto_files.items():
            target_path = file_info['target_path']
            path_parts = target_path.split('/')

            if len(path_parts) >= 4:
                domain = path_parts[3]  # proto/gcommon/v1/{domain}/...
                subdomain = path_parts[4] if len(path_parts) > 4 else 'types'

                key = f"{domain}/{subdomain}"
                if key not in domain_groups:
                    domain_groups[key] = []

                domain_groups[key].append({
                    'current_path': file_info['current_path'],
                    'target_path': file_info['target_path'],
                    'package_name': file_info['package_name'],
                    'go_package': file_info['go_package'],
                    'dependencies': file_info['dependencies'],
                    'issues': file_info['issues']
                })

        # Create domain mappings
        for key, files in domain_groups.items():
            domain, subdomain = key.split('/')

            # Determine migration priority (common first, services last)
            priority = self.get_migration_priority(domain, subdomain)

            # Extract dependencies
            all_deps = set()
            for file_info in files:
                all_deps.update(file_info['dependencies'])

            self.domain_mappings[key] = DomainMapping(
                domain=domain,
                subdomain=subdomain,
                files=files,
                target_package_prefix=f"gcommon.v1.{domain}.{subdomain}",
                go_package_prefix=f"github.com/jdfalk/gcommon/pkg/{domain}/{subdomain}",
                dependencies=list(all_deps),
                migration_priority=priority
            )

    def get_migration_priority(self, domain: str, subdomain: str) -> int:
        """Determine migration priority for a domain/subdomain."""
        # Priority levels (lower = higher priority):
        # 1. Common types (no dependencies)
        # 2. Domain types
        # 3. Configuration
        # 4. APIs
        # 5. Services (highest dependencies)

        if domain == 'common':
            return 1
        elif subdomain == 'types':
            return 2
        elif subdomain == 'config':
            return 3
        elif subdomain in ['api', 'events']:
            return 4
        elif subdomain == 'services':
            return 5
        else:
            return 3  # Default

    def save_domain_mappings(self, output_dir: str):
        """Save individual domain mapping files."""
        os.makedirs(output_dir, exist_ok=True)

        # Sort by priority
        sorted_mappings = sorted(
            self.domain_mappings.items(),
            key=lambda x: x[1].migration_priority
        )

        # Save overall migration order
        migration_order = []
        for key, mapping in sorted_mappings:
            migration_order.append({
                'domain': mapping.domain,
                'subdomain': mapping.subdomain,
                'priority': mapping.migration_priority,
                'file_count': len(mapping.files)
            })

        with open(f"{output_dir}/migration-order.json", 'w') as f:
            json.dump(migration_order, f, indent=2)

        # Save individual domain files
        for key, mapping in self.domain_mappings.items():
            filename = f"{output_dir}/domain-{mapping.domain}-{mapping.subdomain}.json"
            with open(filename, 'w') as f:
                json.dump(asdict(mapping), f, indent=2)

        print(f"Domain mappings saved to {output_dir}/")
        print(f"Total domains: {len(self.domain_mappings)}")
        for key, mapping in sorted_mappings:
            print(f"  {key}: {len(mapping.files)} files (priority {mapping.priority})")

if __name__ == "__main__":
    mapper = DomainMapper("proto-migration-analysis.json")
    mapper.extract_domains()
    mapper.save_domain_mappings("migration-mappings")
```

---
