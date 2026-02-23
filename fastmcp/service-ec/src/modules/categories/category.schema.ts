import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type CategoryDocument = Category & Document;

@Schema({ timestamps: true, versionKey: false })
export class Category {
  @Prop({ required: true, unique: true, trim: true })
  // Display name for the category.
  name!: string;

  @Prop({ trim: true })
  // Optional short description.
  description?: string;
}

export const CategorySchema = SchemaFactory.createForClass(Category);
