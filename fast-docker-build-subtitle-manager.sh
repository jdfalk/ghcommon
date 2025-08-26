#!/bin/bash
# file: fast-docker-build-subtitle-manager.sh
# version: 1.1.0
# guid: 7a8b9c0d-1e2f-3456-7890-abcdef123456

# Fast optimized Docker build for subtitle-manager with aggressive caching

set -euo pipefail

echo "🚀 Starting optimized Docker build for subtitle-manager..."

# Input validation function
validate_input() {
    local var_name="$1"
    local var_value="$2"
    local pattern="$3"
    
    if [[ ! "$var_value" =~ $pattern ]]; then
        echo "Error: Invalid $var_name: $var_value" >&2
        exit 1
    fi
}

# Configuration with input validation
IMAGE_NAME=${IMAGE_NAME:-subtitle-manager}
IMAGE_TAG=${IMAGE_TAG:-latest}
REGISTRY=${REGISTRY:-ghcr.io/jdfalk}
BUILD_CONTEXT=${BUILD_CONTEXT:-.}
DOCKERFILE=${DOCKERFILE:-Dockerfile}

# Validate inputs
validate_input "IMAGE_NAME" "$IMAGE_NAME" '^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
validate_input "IMAGE_TAG" "$IMAGE_TAG" '^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
validate_input "REGISTRY" "$REGISTRY" '^[a-zA-Z0-9][a-zA-Z0-9_.-]*(/[a-zA-Z0-9][a-zA-Z0-9_.-]*)*$'

# Verify required files exist
if [[ ! -f "$DOCKERFILE" ]]; then
    echo "Error: Dockerfile not found at $DOCKERFILE" >&2
    exit 1
fi

if [[ ! -d "$BUILD_CONTEXT" ]]; then
    echo "Error: Build context directory not found at $BUILD_CONTEXT" >&2
    exit 1
fi

# Build arguments - safely obtained
VERSION=${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo "dev")}
BUILD_TIME=${BUILD_TIME:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}
GIT_COMMIT=${GIT_COMMIT:-$(git rev-parse HEAD 2>/dev/null || echo "unknown")}

# Sanitize build arguments to prevent injection
VERSION=$(printf '%s' "$VERSION" | tr -cd '[:alnum:]._-')
BUILD_TIME=$(printf '%s' "$BUILD_TIME" | tr -cd '[:alnum:].:T-')
GIT_COMMIT=$(printf '%s' "$GIT_COMMIT" | tr -cd '[:alnum:]')

# Enable BuildKit for better caching and performance
export DOCKER_BUILDKIT=1

echo "🏗️  Building subtitle-manager with optimized caching..."
echo "   Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "   Version: ${VERSION}"
echo "   Build Time: ${BUILD_TIME}"
echo "   Git Commit: ${GIT_COMMIT}"

# Build with maximum cache utilization and multi-stage optimizations
docker build \
    --file "$DOCKERFILE" \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --tag "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
    --build-arg VERSION="$VERSION" \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    --build-arg GIT_COMMIT="$GIT_COMMIT" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --cache-from "${REGISTRY}/${IMAGE_NAME}:latest" \
    --cache-from "${REGISTRY}/${IMAGE_NAME}:cache" \
    --cache-from "${IMAGE_NAME}:latest" \
    --target final \
    "$BUILD_CONTEXT"

echo "✅ Build completed successfully!"
echo "🔍 Image size:"
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "🧪 Testing image..."
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" --help

echo ""
echo "💡 To run the container:"
echo "docker run -p 8080:8080 -v \$(pwd)/config:/config ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "🐳 To push to registry:"
echo "docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Optional: Create multi-arch build if requested
if [[ "${MULTI_ARCH}" == "true" ]]; then
    echo ""
    echo "🏗️  Creating multi-arch build..."
    
    # Set up buildx if not already done
    docker buildx create --name subtitle-manager-builder --use 2>/dev/null || docker buildx use subtitle-manager-builder
    
    docker buildx build \
        --file "$DOCKERFILE" \
        --platform linux/amd64,linux/arm64 \
        --tag "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_TIME="$BUILD_TIME" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --cache-from "type=registry,ref=${REGISTRY}/${IMAGE_NAME}:cache" \
        --cache-to "type=registry,ref=${REGISTRY}/${IMAGE_NAME}:cache,mode=max" \
        --push \
        "$BUILD_CONTEXT"
    
    echo "✅ Multi-arch build and push completed!"
fi