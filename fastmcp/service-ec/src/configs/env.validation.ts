// Minimal env validation without extra dependencies.
export const validateEnv = () => {
  const { PORT, MONGODB_URI } = process.env;

  if (PORT && Number.isNaN(Number(PORT))) {
    throw new Error('Invalid PORT. It must be a number.');
  }

  if (MONGODB_URI && typeof MONGODB_URI !== 'string') {
    throw new Error('Invalid MONGODB_URI. It must be a string.');
  }
};
