class ErrorResponse extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message) {
    return new ErrorResponse(message, 400);
  }

  static unauthorized(message = 'Not authorized') {
    return new ErrorResponse(message, 401);
  }

  static forbidden(message = 'Forbidden') {
    return new ErrorResponse(message, 403);
  }

  static notFound(message = 'Resource not found') {
    return new ErrorResponse(message, 404);
  }

  static conflict(message = 'Conflict occurred') {
    return new ErrorResponse(message, 409);
  }

  static serverError(message = 'Internal server error') {
    return new ErrorResponse(message, 500);
  }
}

module.exports = ErrorResponse;
