import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types } from 'mongoose';

export type ProductDocument = Product & Document;

@Schema({ timestamps: true, versionKey: false })
export class Product {
  @Prop({ required: true, trim: true })
  // Display name for the product.
  name!: string;

  @Prop({ trim: true })
  // Optional product description.
  description?: string;

  @Prop({ trim: true })
  // Optional product adjective.
  adjective?: string;

  @Prop({ trim: true })
  // Optional product material.
  material?: string;

  @Prop({ required: true })
  // Product price (numeric).
  price!: number;

  @Prop({ type: Types.ObjectId, ref: 'Category', required: true })
  // Related category reference.
  categoryId!: Types.ObjectId;
}

export const ProductSchema = SchemaFactory.createForClass(Product);
