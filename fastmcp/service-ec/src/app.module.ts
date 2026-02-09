import { Module } from '@nestjs/common';
import { DatabaseModule } from './configs/database.config';
import { CategoriesModule } from './modules/categories/categories.module';
import { ProductsModule } from './modules/products/products.module';

@Module({
  imports: [
    // MongoDB connection (default to local db_ec).
    DatabaseModule,
    // Feature modules.
    CategoriesModule,
    ProductsModule,
  ],
})
export class AppModule {}
