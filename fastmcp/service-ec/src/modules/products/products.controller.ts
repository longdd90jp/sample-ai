import { Body, Controller, Delete, Get, Param, Patch, Post, Query } from '@nestjs/common';
import { ProductsService } from './products.service';
import { CreateProductDto, UpdateProductDto } from './product.dto';

@Controller('products')
export class ProductsController {
  constructor(private readonly productsService: ProductsService) {}

  @Post()
  create(@Body() dto: CreateProductDto) {
    // Create a new product.
    return this.productsService.create(dto);
  }

  @Get()
  findAll() {
    // List all products.
    return this.productsService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    // Fetch a product by id.
    return this.productsService.findOne(id);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() dto: UpdateProductDto) {
    // Update a product by id.
    return this.productsService.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    // Delete a product by id.
    return this.productsService.remove(id);
  }

  @Post('faker')
  faker(@Query('count') count = '10') {
    // Create faker products; count is passed via query.
    return this.productsService.fakerCreate(Number(count));
  }
}
