import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Category, CategoryDocument } from './category.schema';
import { CreateCategoryDto, UpdateCategoryDto } from './category.dto';

let fakerInstance: typeof import('@faker-js/faker').faker | null = null;

async function getFaker() {
  if (!fakerInstance) {
    // Use eval to keep dynamic import from being downleveled to require() in CJS builds.
    const mod = await (0, eval)('import("@faker-js/faker")');
    fakerInstance = mod.faker;
  }
  return fakerInstance;
}

@Injectable()
export class CategoriesService {
  constructor(
    @InjectModel(Category.name) private readonly categoryModel: Model<CategoryDocument>,
  ) { }

  async create(dto: CreateCategoryDto) {
    // Create a category document from DTO payload.
    const created = new this.categoryModel(dto);
    return created.save();
  }

  async findAll() {
    // Return all categories, newest first.
    return this.categoryModel.find().sort({ createdAt: -1 }).lean();
  }

  async findOne(id: string) {
    // Look up a category by MongoDB ObjectId.
    const category = await this.categoryModel.findById(id).lean();
    if (!category) {
      throw new NotFoundException('Category not found');
    }
    return category;
  }

  async update(id: string, dto: UpdateCategoryDto) {
    // Update a category and return the modified document.
    const updated = await this.categoryModel
      .findByIdAndUpdate(id, dto, { new: true })
      .lean();
    if (!updated) {
      throw new NotFoundException('Category not found');
    }
    return updated;
  }

  async remove(id: string) {
    // Delete a category by id.
    const removed = await this.categoryModel.findByIdAndDelete(id).lean();
    if (!removed) {
      throw new NotFoundException('Category not found');
    }
    return removed;
  }

  async fakerCreate(count: number) {
    const faker = await getFaker();
    // Clamp requested count to a safe range.
    const requested = Math.max(1, Math.min(count, 1000));
    // Build a set of existing category names to avoid duplicates.
    const existing = await this.categoryModel.find().select('name').lean();
    const existingNames = new Set(existing.map((c) => c.name));

    const toCreate: Array<Pick<Category, 'name' | 'description'>> = [];
    // Guard against infinite loops when faker returns duplicates.
    const maxAttempts = requested * 5;
    let attempts = 0;

    while (toCreate.length < requested && attempts < maxAttempts) {
      attempts += 1;
      const name = faker.commerce.department();
      // Skip if category name already exists.
      if (existingNames.has(name)) {
        continue;
      }
      existingNames.add(name);
      toCreate.push({
        name,
        description: faker.food.description()
      });
    }

    if (toCreate.length === 0) {
      return {
        requested,
        inserted: 0,
        skippedExisting: requested,
      };
    }

    // Insert new categories in bulk; duplicates should already be filtered out.
    const inserted = await this.categoryModel.insertMany(toCreate, {
      ordered: false,
    });

    return {
      requested,
      inserted: inserted.length,
      skippedExisting: requested - inserted.length,
    };
  }
}
