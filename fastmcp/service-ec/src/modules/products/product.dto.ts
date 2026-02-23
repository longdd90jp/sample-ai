import { IsMongoId, IsNumber, IsOptional, IsString, MaxLength, Min } from 'class-validator';
import { Type } from 'class-transformer';

export class CreateProductDto {
  // Product name.
  @IsString()
  @MaxLength(150)
  name!: string;

  // Optional description.
  @IsOptional()
  @IsString()
  @MaxLength(500)
  description?: string;

  // Optional adjective.
  @IsOptional()
  @IsString()
  @MaxLength(100)
  adjective?: string;

  // Optional material.
  @IsOptional()
  @IsString()
  @MaxLength(100)
  material?: string;

  // Numeric price.
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  price!: number;

  // Category ObjectId.
  @IsMongoId()
  categoryId!: string;
}

export class UpdateProductDto {
  // New name, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(150)
  name?: string;

  // New description, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(500)
  description?: string;

  // New adjective, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(100)
  adjective?: string;

  // New material, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(100)
  material?: string;

  // New price, if provided.
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  price?: number;

  // New category id, if provided.
  @IsOptional()
  @IsMongoId()
  categoryId?: string;
}
