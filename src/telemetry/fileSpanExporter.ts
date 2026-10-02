import { ExportResultCode } from '@opentelemetry/core';
import {
  ReadableSpan,
  SpanExporter,
} from '@opentelemetry/sdk-trace-base';
import { appendFileSync } from 'node:fs';

export class NdjsonFileSpanExporter implements SpanExporter {
  public constructor(private readonly outputPath: string) {}

  public export(spans: ReadableSpan[], resultCallback: (result: { code: ExportResultCode }) => void): void {
    try {
      for (const span of spans) {
        const serialized = {
          traceId: span.spanContext().traceId,
          spanId: span.spanContext().spanId,
          name: span.name,
          kind: span.kind,
          startTime: span.startTime,
          endTime: span.endTime,
          attributes: span.attributes,
          status: span.status,
          events: span.events,
        };
        appendFileSync(this.outputPath, `${JSON.stringify(serialized)}\n`, 'utf8');
      }
      resultCallback({ code: ExportResultCode.SUCCESS });
    } catch {
      resultCallback({ code: ExportResultCode.FAILED });
    }
  }

  public forceFlush(): Promise<void> {
    return Promise.resolve();
  }

  public shutdown(): Promise<void> {
    return Promise.resolve();
  }
}
