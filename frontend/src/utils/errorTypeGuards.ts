/**
 * Type guards for error handling with proper TypeScript type safety
 */

// Base error with response
interface ErrorWithResponse {
  response: {
    status: number;
    data?: any;
  };
  message?: string;
}

// Error with validation errors
interface ErrorWithValidationErrors extends ErrorWithResponse {
  response: {
    status: number;
    data: {
      [key: string]: string | string[];
    };
  };
}

// Error with specific error fields
interface ErrorWithData extends ErrorWithResponse {
  response: {
    status: number;
    data: {
      error?: string;
      errors?: string[];
      detail?: string;
      message?: string;
      non_field_errors?: string[];
      tax_number?: string[];
      partner_name?: string[];
      [key: string]: any;
    };
  };
}

// Error with message
interface ErrorWithMessage {
  message: string;
}

// Error with config (axios specific)
interface ErrorWithConfig {
  config: any;
  response?: {
    status: number;
    data?: any;
  };
}

/**
 * Check if error has a response with status
 */
export function hasResponseStatus(error: unknown): error is ErrorWithResponse {
  if (typeof error !== 'object' || error === null) return false;
  if (!('response' in error)) return false;

  const errorWithResponse = error as { response: unknown };
  if (typeof errorWithResponse.response !== 'object' || errorWithResponse.response === null)
    return false;
  if (!('status' in errorWithResponse.response)) return false;

  const response = errorWithResponse.response as { status: unknown };
  return typeof response.status === 'number';
}

/**
 * Check if error has response.data (for accessing error details)
 */
export function hasResponseData(error: unknown): error is ErrorWithData {
  if (!hasResponseStatus(error)) return false;
  const errorWithResponse = error as ErrorWithResponse;
  return (
    'data' in errorWithResponse.response &&
    typeof errorWithResponse.response.data === 'object' &&
    errorWithResponse.response.data !== null
  );
}

/**
 * Check if error has validation errors (400 with field-specific errors)
 */
export function hasValidationErrors(error: unknown): error is ErrorWithValidationErrors {
  if (!hasResponseData(error)) return false;
  const errorWithData = error as ErrorWithData;
  return (
    errorWithData.response.status === 400 &&
    typeof errorWithData.response.data === 'object' &&
    errorWithData.response.data !== null
  );
}

/**
 * Check if error has a message property
 */
export function hasMessage(error: unknown): error is ErrorWithMessage {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as ErrorWithMessage).message === 'string'
  );
}

/**
 * Check if error has config property (axios error)
 */
export function hasConfig(error: unknown): error is ErrorWithConfig {
  return (
    typeof error === 'object' &&
    error !== null &&
    'config' in error &&
    typeof (error as ErrorWithConfig).config === 'object'
  );
}

/**
 * Get error message from various error types
 */
export function getErrorMessage(error: unknown, fallback = 'An unknown error occurred'): string {
  if (hasResponseData(error)) {
    const { data } = error.response;
    if (data.error && typeof data.error === 'string') return data.error;
    if (data.detail && typeof data.detail === 'string') return data.detail;
    if (data.message && typeof data.message === 'string') return data.message;
    if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
      const firstError = data.non_field_errors[0];
      return typeof firstError === 'string' ? firstError : fallback;
    }
    if (data.errors && Array.isArray(data.errors)) {
      const stringErrors = data.errors.filter((e): e is string => typeof e === 'string');
      return stringErrors.length > 0 ? stringErrors.join('\n\n') : fallback;
    }
  }

  if (hasMessage(error)) {
    return error.message;
  }

  return fallback;
}

/**
 * Check if error is a 401 (Unauthorized)
 */
export function isUnauthorized(error: unknown): boolean {
  return hasResponseStatus(error) && error.response.status === 401;
}

/**
 * Check if error is a 403 (Forbidden)
 */
export function isForbidden(error: unknown): boolean {
  return hasResponseStatus(error) && error.response.status === 403;
}

/**
 * Check if error is a 400 (Bad Request)
 */
export function isBadRequest(error: unknown): boolean {
  return hasResponseStatus(error) && error.response.status === 400;
}
