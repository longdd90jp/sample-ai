import { IsOptional, IsString, MaxLength } from 'class-validator';

export class CreateCategoryDto {
  // Category name (unique).
  @IsString()
  @MaxLength(100)
  name!: string;

  // Optional description.
  @IsOptional()
  @IsString()
  @MaxLength(255)
  description?: string;
}

export class UpdateCategoryDto {
  // New name, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(100)
  name?: string;

  // New description, if provided.
  @IsOptional()
  @IsString()
  @MaxLength(255)
  description?: string;
}
