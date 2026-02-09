import { Body, Controller, Delete, Get, Param, Patch, Post, Query } from '@nestjs/common';
import { CategoriesService } from './categories.service';
import { CreateCategoryDto, UpdateCategoryDto } from './category.dto';

@Controller('categories')
export class CategoriesController {
  constructor(private readonly categoriesService: CategoriesService) {}

  @Post()
  create(@Body() dto: CreateCategoryDto) {
    // Create a new category.
    return this.categoriesService.create(dto);
  }

  @Get()
  findAll() {
    // List all categories.
    return this.categoriesService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    // Fetch a category by id.
    return this.categoriesService.findOne(id);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() dto: UpdateCategoryDto) {
    // Update a category by id.
    return this.categoriesService.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    // Delete a category by id.
    return this.categoriesService.remove(id);
  }

  @Post('faker')
  faker(@Query('count') count = '10') {
    // Create faker categories; count is passed via query.
    return this.categoriesService.fakerCreate(Number(count));
  }
}
