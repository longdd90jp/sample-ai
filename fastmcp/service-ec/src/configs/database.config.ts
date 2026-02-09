import { MongooseModule } from '@nestjs/mongoose';

// Centralized database configuration.
export const DatabaseModule = MongooseModule.forRoot(
  process.env.MONGODB_URI || 'mongodb://localhost:27017/db_ec',
);
