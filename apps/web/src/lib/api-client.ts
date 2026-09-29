import { z } from "zod";

import { clientEnv } from "@/lib/env";

const apiErrorSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    request_id: z.string().optional(),
    details: z.unknown().optional(),
  }),
});

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "UNKNOWN_ERROR",
    readonly requestId?: string,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiRequestOptions<T> = RequestInit & {
  schema?: z.ZodType<T>;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions<T> = {},
): Promise<T> {
  const { schema, headers, ...requestOptions } = options;
  const response = await fetch(
    new URL(path, clientEnv.NEXT_PUBLIC_API_BASE_URL),
    {
      ...requestOptions,
      headers: {
        Accept: "application/json",
        ...(requestOptions.body ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
    },
  );

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const parsedError = apiErrorSchema.safeParse(payload);

    if (parsedError.success) {
      throw new ApiError(
        parsedError.data.error.message,
        response.status,
        parsedError.data.error.code,
        parsedError.data.error.request_id,
        parsedError.data.error.details,
      );
    }

    throw new ApiError(
      `API request failed with status ${response.status}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload: unknown = await response.json();
  return schema ? schema.parse(payload) : (payload as T);
}
