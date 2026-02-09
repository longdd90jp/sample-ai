import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { faker } from '@faker-js/faker';
import { Product, ProductDocument } from './product.schema';
import { CreateProductDto, UpdateProductDto } from './product.dto';
import { Category, CategoryDocument } from '../categories/category.schema';

@Injectable()
export class ProductsService {
  constructor(
    @InjectModel(Product.name) private readonly productModel: Model<ProductDocument>,
    @InjectModel(Category.name) private readonly categoryModel: Model<CategoryDocument>,
  ) {}

  async create(dto: CreateProductDto) {
    // Create a product document from DTO payload.
    const created = new this.productModel(dto);
    return created.save();
  }

  async findAll() {
    // Return all products with category name populated.
    return this.productModel
      .find()
      .populate('categoryId', 'name')
      .sort({ createdAt: -1 })
      .lean();
  }

  async findOne(id: string) {
    // Look up a product by MongoDB ObjectId.
    const product = await this.productModel
      .findById(id)
      .populate('categoryId', 'name')
      .lean();
    if (!product) {
      throw new NotFoundException('Product not found');
    }
    return product;
  }

  async update(id: string, dto: UpdateProductDto) {
    // Update a product and return the modified document.
    const updated = await this.productModel
      .findByIdAndUpdate(id, dto, { new: true })
      .populate('categoryId', 'name')
      .lean();
    if (!updated) {
      throw new NotFoundException('Product not found');
    }
    return updated;
  }

  async remove(id: string) {
    // Delete a product by id.
    const removed = await this.productModel.findByIdAndDelete(id).lean();
    if (!removed) {
      throw new NotFoundException('Product not found');
    }
    return removed;
  }

  async fakerCreate(count: number) {
    // Clamp requested count to a safe range.
    const requested = Math.max(1, Math.min(count, 1000));
    // Fetch available categories to pick a random categoryId.
    const categories = await this.categoryModel.find().select('_id').lean();
    if (categories.length === 0) {
      throw new BadRequestException('No categories available for faker products');
    }

    const toCreate: Array<Pick<Product, 'name' | 'description' | 'price' | 'categoryId'>> = [];
    for (let i = 0; i < requested; i += 1) {
      // Choose a random category for each product.
      const category = categories[Math.floor(Math.random() * categories.length)];
      toCreate.push({
        name: faker.commerce.productName(),
        description: faker.commerce.productDescription(),
        price: Number(faker.commerce.price({ min: 1, max: 10000, dec: 2 })),
        categoryId: category._id,
      });
    }

    // Insert faker products in bulk.
    const inserted = await this.productModel.insertMany(toCreate, { ordered: false });
    return {
      requested,
      inserted: inserted.length,
    };
  }
}
