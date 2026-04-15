import { AppError } from './app-error.js';

export class ValidationError extends AppError {
  constructor(message = 'Validation error') {
    super(message, 400, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}
