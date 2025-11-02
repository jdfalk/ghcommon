<!-- file: docs/cross-registry-todos/task-17/t17-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t17-observability-logging-part2-m7n8o9p0-q1r2 -->

# Task 17 Part 2: JavaScript/TypeScript Structured Logging

## JavaScript Structured Logging with Winston

### Winston Configuration

```typescript
// file: src/logging/winston-config.ts
// version: 1.0.0
// guid: typescript-winston-config

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

export interface LoggerConfig {
  level: string;
  service: string;
  environment: string;
  logFile?: string;
}

/**
 * Create Winston logger with JSON formatting
 */
export function createLogger(config: LoggerConfig): winston.Logger {
  const { level, service, environment, logFile } = config;

  // Custom format for structured logging
  const structuredFormat = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSSZ' }),
    winston.format.errors({ stack: true }),
    winston.format.metadata({
      fillExcept: ['timestamp', 'level', 'message', 'service', 'environment'],
    }),
    winston.format.json()
  );

  const transports: winston.transport[] = [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, metadata }) => {
          const meta = Object.keys(metadata).length > 0 ? JSON.stringify(metadata, null, 2) : '';
          return `${timestamp} [${level}] ${message} ${meta}`;
        })
      ),
    }),
  ];

  // File transport with daily rotation
  if (logFile) {
    transports.push(
      new DailyRotateFile({
        filename: `${logFile}-%DATE%.log`,
        datePattern: 'YYYY-MM-DD',
        maxSize: '20m',
        maxFiles: '14d',
        format: structuredFormat,
      })
    );
  }

  const logger = winston.createLogger({
    level,
    defaultMeta: { service, environment },
    format: structuredFormat,
    transports,
  });

  logger.info('Logger initialized', {
    level,
    service,
    environment,
    logFile: logFile || 'console-only',
  });

  return logger;
}

/**
 * Child logger with additional context
 */
export function createChildLogger(
  parent: winston.Logger,
  context: Record<string, any>
): winston.Logger {
  return parent.child(context);
}
```

### Express Middleware

```typescript
// file: src/middleware/logging.ts
// version: 1.0.0
// guid: typescript-express-logging-middleware

import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import winston from 'winston';

declare global {
  namespace Express {
    interface Request {
      requestId: string;
      logger: winston.Logger;
      startTime: number;
    }
  }
}

/**
 * Logging middleware for Express
 */
export function loggingMiddleware(logger: winston.Logger) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Generate request ID
    const requestId = uuidv4();
    req.requestId = requestId;
    req.startTime = Date.now();

    // Create child logger with request context
    req.logger = logger.child({
      requestId,
      method: req.method,
      path: req.path,
      remoteAddr: req.ip || req.socket.remoteAddress,
      userAgent: req.get('user-agent'),
    });

    // Log request start
    req.logger.info('HTTP request started', {
      query: req.query,
      body: sanitizeBody(req.body),
    });

    // Capture response
    const originalSend = res.send;
    res.send = function (data: any) {
      const duration = Date.now() - req.startTime;
      const status = res.statusCode;

      // Log based on status
      const logLevel = status >= 500 ? 'error' : status >= 400 ? 'warn' : 'info';

      req.logger.log(logLevel, 'HTTP request completed', {
        status,
        durationMs: duration,
      });

      // Set response header
      res.setHeader('X-Request-ID', requestId);

      return originalSend.call(this, data);
    };

    // Handle errors
    res.on('error', (error: Error) => {
      const duration = Date.now() - req.startTime;

      req.logger.error('HTTP request error', {
        status: res.statusCode || 500,
        durationMs: duration,
        error: error.message,
        stack: error.stack,
      });
    });

    next();
  };
}

/**
 * Sanitize request body to remove sensitive data
 */
function sanitizeBody(body: any): any {
  if (!body || typeof body !== 'object') {
    return body;
  }

  const sensitiveFields = ['password', 'token', 'apiKey', 'secret', 'creditCard', 'ssn'];

  const sanitized = { ...body };

  for (const field of sensitiveFields) {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}

/**
 * Error logging middleware
 */
export function errorLoggingMiddleware(logger: winston.Logger) {
  return (err: Error, req: Request, res: Response, next: NextFunction) => {
    const requestLogger = req.logger || logger;

    requestLogger.error('Unhandled error in request', {
      error: err.message,
      stack: err.stack,
      method: req.method,
      path: req.path,
      requestId: req.requestId,
    });

    next(err);
  };
}
```

## Pino High-Performance Logging

### Pino Configuration

```typescript
// file: src/logging/pino-config.ts
// version: 1.0.0
// guid: typescript-pino-config

import pino from 'pino';
import pinoHttp from 'pino-http';
import { Request, Response } from 'express';

export interface PinoConfig {
  level: string;
  service: string;
  environment: string;
  prettyPrint?: boolean;
}

/**
 * Create Pino logger
 */
export function createPinoLogger(config: PinoConfig): pino.Logger {
  const { level, service, environment, prettyPrint = false } = config;

  const logger = pino({
    level,
    base: {
      service,
      environment,
      pid: process.pid,
      hostname: require('os').hostname(),
    },
    timestamp: pino.stdTimeFunctions.isoTime,
    formatters: {
      level(label: string) {
        return { level: label };
      },
      bindings(bindings: pino.Bindings) {
        return {
          pid: bindings.pid,
          hostname: bindings.hostname,
        };
      },
    },
    serializers: {
      req: pino.stdSerializers.req,
      res: pino.stdSerializers.res,
      err: pino.stdSerializers.err,
    },
    ...(prettyPrint && {
      transport: {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'SYS:standard',
          ignore: 'pid,hostname',
        },
      },
    }),
  });

  logger.info({ level, service, environment }, 'Pino logger initialized');

  return logger;
}

/**
 * Pino HTTP middleware
 */
export function createPinoHttpMiddleware(logger: pino.Logger) {
  return pinoHttp({
    logger,
    customLogLevel: (req: Request, res: Response, err?: Error) => {
      if (res.statusCode >= 500 || err) {
        return 'error';
      }
      if (res.statusCode >= 400) {
        return 'warn';
      }
      return 'info';
    },
    customSuccessMessage: (req: Request, res: Response) => {
      return `${req.method} ${req.url} completed`;
    },
    customErrorMessage: (req: Request, res: Response, err: Error) => {
      return `${req.method} ${req.url} failed: ${err.message}`;
    },
    customAttributeKeys: {
      req: 'request',
      res: 'response',
      err: 'error',
      responseTime: 'durationMs',
    },
    customProps: (req: Request, res: Response) => ({
      requestId: req.headers['x-request-id'] || require('uuid').v4(),
      userAgent: req.get('user-agent'),
      remoteAddr: req.ip || req.socket.remoteAddress,
    }),
    serializers: {
      req(req: Request) {
        return {
          method: req.method,
          url: req.url,
          path: req.path,
          query: req.query,
          headers: sanitizeHeaders(req.headers),
        };
      },
      res(res: Response) {
        return {
          statusCode: res.statusCode,
          headers: sanitizeHeaders(res.getHeaders()),
        };
      },
    },
  });
}

/**
 * Sanitize headers to remove sensitive data
 */
function sanitizeHeaders(headers: any): any {
  const sanitized = { ...headers };
  const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key'];

  for (const header of sensitiveHeaders) {
    if (header in sanitized) {
      sanitized[header] = '[REDACTED]';
    }
  }

  return sanitized;
}
```

## Go Structured Logging

### Zap Configuration

```go
// file: logging/zap.go
// version: 1.0.0
// guid: go-zap-logging-config

package logging

import (
 "os"
 "time"

 "go.uber.org/zap"
 "go.uber.org/zap/zapcore"
 "gopkg.in/natefinch/lumberjack.v2"
)

// Config holds logging configuration
type Config struct {
 Level       string
 Service     string
 Environment string
 LogFile     string
 MaxSize     int // megabytes
 MaxBackups  int
 MaxAge      int // days
}

// NewLogger creates a new Zap logger
func NewLogger(cfg Config) (*zap.Logger, error) {
 // Parse log level
 level := zap.NewAtomicLevel()
 if err := level.UnmarshalText([]byte(cfg.Level)); err != nil {
  return nil, err
 }

 // Encoder config
 encoderConfig := zapcore.EncoderConfig{
  TimeKey:        "timestamp",
  LevelKey:       "level",
  NameKey:        "logger",
  CallerKey:      "caller",
  FunctionKey:    zapcore.OmitKey,
  MessageKey:     "message",
  StacktraceKey:  "stacktrace",
  LineEnding:     zapcore.DefaultLineEnding,
  EncodeLevel:    zapcore.LowercaseLevelEncoder,
  EncodeTime:     zapcore.ISO8601TimeEncoder,
  EncodeDuration: zapcore.SecondsDurationEncoder,
  EncodeCaller:   zapcore.ShortCallerEncoder,
 }

 // Create cores
 var cores []zapcore.Core

 // Console core
 consoleEncoder := zapcore.NewJSONEncoder(encoderConfig)
 consoleCore := zapcore.NewCore(
  consoleEncoder,
  zapcore.AddSync(os.Stdout),
  level,
 )
 cores = append(cores, consoleCore)

 // File core with rotation
 if cfg.LogFile != "" {
  fileWriter := zapcore.AddSync(&lumberjack.Logger{
   Filename:   cfg.LogFile,
   MaxSize:    cfg.MaxSize,
   MaxBackups: cfg.MaxBackups,
   MaxAge:     cfg.MaxAge,
   Compress:   true,
  })

  fileEncoder := zapcore.NewJSONEncoder(encoderConfig)
  fileCore := zapcore.NewCore(
   fileEncoder,
   fileWriter,
   level,
  )
  cores = append(cores, fileCore)
 }

 // Create logger
 core := zapcore.NewTee(cores...)
 logger := zap.New(core,
  zap.AddCaller(),
  zap.AddStacktrace(zapcore.ErrorLevel),
  zap.Fields(
   zap.String("service", cfg.Service),
   zap.String("environment", cfg.Environment),
  ),
 )

 logger.Info("Logger initialized",
  zap.String("level", cfg.Level),
  zap.String("service", cfg.Service),
  zap.String("environment", cfg.Environment),
 )

 return logger, nil
}

// HTTPRequestFields returns common HTTP request log fields
func HTTPRequestFields(
 method, path, requestID, remoteAddr, userAgent string,
 status int,
 duration time.Duration,
) []zap.Field {
 return []zap.Field{
  zap.String("method", method),
  zap.String("path", path),
  zap.Int("status", status),
  zap.Duration("duration", duration),
  zap.String("request_id", requestID),
  zap.String("remote_addr", remoteAddr),
  zap.String("user_agent", userAgent),
 }
}

// DatabaseFields returns database operation log fields
func DatabaseFields(
 operation, table string,
 duration time.Duration,
 rowsAffected int64,
 err error,
) []zap.Field {
 fields := []zap.Field{
  zap.String("operation", operation),
  zap.String("table", table),
  zap.Duration("duration", duration),
  zap.Int64("rows_affected", rowsAffected),
 }

 if err != nil {
  fields = append(fields, zap.Error(err))
 }

 return fields
}
```

### Gin Middleware

```go
// file: middleware/logging.go
// version: 1.0.0
// guid: go-gin-logging-middleware

package middleware

import (
 "time"

 "github.com/gin-gonic/gin"
 "github.com/google/uuid"
 "go.uber.org/zap"
)

// LoggingMiddleware creates a Gin middleware for logging
func LoggingMiddleware(logger *zap.Logger) gin.HandlerFunc {
 return func(c *gin.Context) {
  // Generate request ID
  requestID := uuid.New().String()
  c.Set("request_id", requestID)
  c.Header("X-Request-ID", requestID)

  // Start timer
  start := time.Now()

  // Extract request info
  method := c.Request.Method
  path := c.Request.URL.Path
  query := c.Request.URL.RawQuery
  remoteAddr := c.ClientIP()
  userAgent := c.Request.UserAgent()

  // Create child logger
  reqLogger := logger.With(
   zap.String("request_id", requestID),
   zap.String("method", method),
   zap.String("path", path),
   zap.String("remote_addr", remoteAddr),
   zap.String("user_agent", userAgent),
  )

  // Store logger in context
  c.Set("logger", reqLogger)

  // Log request start
  reqLogger.Info("HTTP request started",
   zap.String("query", query),
  )

  // Process request
  c.Next()

  // Calculate duration
  duration := time.Since(start)
  status := c.Writer.Status()

  // Determine log level based on status
  logFunc := reqLogger.Info
  if status >= 500 {
   logFunc = reqLogger.Error
  } else if status >= 400 {
   logFunc = reqLogger.Warn
  }

  // Log request completion
  logFunc("HTTP request completed",
   zap.Int("status", status),
   zap.Duration("duration", duration),
   zap.Int("size", c.Writer.Size()),
  )
 }
}

// RecoveryMiddleware logs panics and recovers
func RecoveryMiddleware(logger *zap.Logger) gin.HandlerFunc {
 return func(c *gin.Context) {
  defer func() {
   if err := recover(); err != nil {
    // Get logger from context
    reqLogger, exists := c.Get("logger")
    if !exists {
     reqLogger = logger
    }

    reqLogger.(*zap.Logger).Error("Panic recovered",
     zap.Any("error", err),
     zap.String("method", c.Request.Method),
     zap.String("path", c.Request.URL.Path),
    )

    // Return 500 error
    c.AbortWithStatus(500)
   }
  }()

  c.Next()
 }
}

// GetLogger retrieves the logger from Gin context
func GetLogger(c *gin.Context) *zap.Logger {
 logger, exists := c.Get("logger")
 if !exists {
  // Fallback to global logger
  return zap.L()
 }
 return logger.(*zap.Logger)
}
```

## Sensitive Data Masking

### PII Redaction

```typescript
// file: src/logging/sanitization.ts
// version: 1.0.0
// guid: typescript-log-sanitization

/**
 * Sensitive data patterns
 */
const PATTERNS = {
  email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
  creditCard: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
  ssn: /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g,
  phone: /\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
  ipv4: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
  jwt: /eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*/g,
};

/**
 * Sensitive field names
 */
const SENSITIVE_FIELDS = new Set([
  'password',
  'token',
  'apiKey',
  'api_key',
  'secret',
  'creditCard',
  'credit_card',
  'ssn',
  'authorization',
  'cookie',
]);

/**
 * Mask sensitive data in string
 */
export function maskSensitiveData(text: string): string {
  let masked = text;

  // Mask patterns
  masked = masked.replace(PATTERNS.email, match => {
    const [local, domain] = match.split('@');
    return `${local[0]}***@${domain}`;
  });

  masked = masked.replace(PATTERNS.creditCard, () => '**** **** **** ****');
  masked = masked.replace(PATTERNS.ssn, () => '***-**-****');
  masked = masked.replace(PATTERNS.phone, () => '***-***-****');
  masked = masked.replace(PATTERNS.jwt, () => '[JWT_TOKEN]');

  return masked;
}

/**
 * Sanitize object recursively
 */
export function sanitizeObject<T>(obj: T, maxDepth = 5): T {
  if (maxDepth === 0 || obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeObject(item, maxDepth - 1)) as any;
  }

  const sanitized: any = {};

  for (const [key, value] of Object.entries(obj)) {
    // Check if field is sensitive
    if (SENSITIVE_FIELDS.has(key.toLowerCase())) {
      sanitized[key] = '[REDACTED]';
      continue;
    }

    // Recursively sanitize objects
    if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeObject(value, maxDepth - 1);
    } else if (typeof value === 'string') {
      sanitized[key] = maskSensitiveData(value);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized as T;
}

/**
 * Create sanitizing logger wrapper
 */
export function createSanitizingLogger(logger: any) {
  return new Proxy(logger, {
    get(target, prop: string) {
      const original = target[prop];

      // Intercept log methods
      if (
        typeof original === 'function' &&
        ['log', 'info', 'warn', 'error', 'debug'].includes(prop)
      ) {
        return function (...args: any[]) {
          const sanitized = args.map(arg => (typeof arg === 'object' ? sanitizeObject(arg) : arg));
          return original.apply(target, sanitized);
        };
      }

      return original;
    },
  });
}
```

---

**Part 2 Complete**: JavaScript/TypeScript structured logging with Winston configuration including
custom formats and daily rotation, Express logging middleware with request IDs and child loggers,
Pino high-performance logging with custom serializers, Go Zap logging with JSON encoding and file
rotation, Gin middleware with request/response logging and panic recovery, comprehensive sensitive
data masking with PII redaction patterns for emails/credit cards/SSNs/JWTs and recursive object
sanitization. ✅

**Continue to Part 3** for log correlation with trace IDs, OpenTelemetry integration, and
distributed tracing context propagation.
