import { context, Span, SpanStatusCode, trace } from '@opentelemetry/api';
import { Resource } from '@opentelemetry/resources';
import { NodeSDK } from '@opentelemetry/sdk-node';
import {
  BatchSpanProcessor,
  ConsoleSpanExporter,
  MultiSpanProcessor,
} from '@opentelemetry/sdk-trace-base';
import { AppEnv } from '../config/env.js';
import { NdjsonFileSpanExporter } from './fileSpanExporter.js';

export const initTelemetry = (env: AppEnv): NodeSDK => {
  const resource = new Resource({
    'service.name': 'rlm-mastra-style-agent',
    'service.version': '0.1.0',
    'deployment.environment': env.NODE_ENV,
  });

  const sdk = new NodeSDK({
    resource,
    spanProcessor: new MultiSpanProcessor([
      new BatchSpanProcessor(new ConsoleSpanExporter()),
      new BatchSpanProcessor(new NdjsonFileSpanExporter(env.TRACE_FILE_PATH)),
    ]),
  });

  void sdk.start();
  return sdk;
};

export const withSpan = async <T>(
  name: string,
  attributes: Record<string, string | number | boolean>,
  fn: (span: Span) => Promise<T>,
): Promise<T> => {
  const tracer = trace.getTracer('rlm-tracer');

  return tracer.startActiveSpan(name, { attributes }, async (span) => {
    try {
      const output = await context.with(trace.setSpan(context.active(), span), () => fn(span));
      span.setStatus({ code: SpanStatusCode.OK });
      return output;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error instanceof Error ? error.message : 'Unknown failure',
      });
      throw error;
    } finally {
      span.end();
    }
  });
};
