/**
 * Patel Automobiles - MongoDB Atlas Connection & Schema Models
 * Use this file to connect your Node.js / Serverless / Express / Vercel backend directly to MongoDB Atlas.
 */

const mongoose = require('mongoose');

// MongoDB Atlas Connection URI
const MONGODB_URI = process.env.MONGODB_URI || "mongodb+srv://patelautomobile:patelautomobile123@cluster0.mongodb.net/patelautomobile?retryWrites=true&w=majority";

const connectMongoDB = async () => {
  try {
    await mongoose.connect(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log("✅ MongoDB Atlas Connected Successfully for Patel Automobiles!");
  } catch (error) {
    console.error("❌ MongoDB Atlas Connection Error:", error);
  }
};

// 1. Service Booking Schema
const BookingSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  customer_name: { type: String, required: true },
  mobile_number: { type: String, required: true },
  vehicle_number: { type: String, required: true },
  bike_model: { type: String, default: 'Two Wheeler' },
  complaint: { type: String, default: 'General Service' },
  preferred_date: { type: String, required: true },
  preferred_time: { type: String, required: true },
  status: { type: String, enum: ['PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED'], default: 'PENDING' },
  created_at: { type: Date, default: Date.now }
});

// 2. Workshop Job Card Schema
const JobSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  customer_name: { type: String, required: true },
  mobile_number: { type: String, required: true },
  vehicle_number: { type: String, required: true },
  bike_model: { type: String, default: 'Two Wheeler' },
  complaint: { type: String, default: 'General Repair' },
  assigned_mechanic: { type: String, default: 'Patel Owner' },
  secondary_mechanic: { type: String, default: '' },
  labour_charge: { type: Number, default: 300 },
  parts_total: { type: Number, default: 0 },
  live_total: { type: Number, default: 300 },
  status: { type: String, enum: ['IN_PROGRESS', 'FINISHED', 'CANCELLED'], default: 'IN_PROGRESS' },
  parts: [{
    part_name: String,
    price: Number,
    quantity: Number,
    staged_total: Number
  }],
  created_at: { type: Date, default: Date.now },
  completed_at: Date
});

// 3. Inventory Spare Part Schema
const InventorySchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  part_name: { type: String, required: true },
  category: { type: String, default: 'General' },
  price: { type: Number, required: true },
  current_stock: { type: Number, default: 10 },
  min_stock_alert: { type: Number, default: 2 },
  updated_at: { type: Date, default: Date.now }
});

// 4. Customer Directory Schema
const CustomerSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  customer_name: { type: String, required: true },
  mobile_number: { type: String, required: true },
  vehicle_number: { type: String, default: 'GJ-15' },
  bike_model: { type: String, default: 'Two Wheeler' },
  total_bills: { type: Number, default: 0 },
  total_spent: { type: Number, default: 0 },
  created_at: { type: Date, default: Date.now }
});

// 5. Billing Invoice Schema
const BillingSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  invoice_number: { type: String, required: true, unique: true },
  customer_name: { type: String, required: true },
  mobile_number: { type: String, required: true },
  vehicle_number: { type: String, required: true },
  bike_model: { type: String, default: 'Two Wheeler' },
  labour_charge: { type: Number, default: 300 },
  parts_total: { type: Number, default: 0 },
  total_amount: { type: Number, required: true },
  paid_amount: { type: Number, required: true },
  discount_amount: { type: Number, default: 0 },
  payment_status: { type: String, enum: ['PAID', 'PARTIAL', 'UNPAID'], default: 'PAID' },
  created_at: { type: Date, default: Date.now }
});

const Booking = mongoose.model('Booking', BookingSchema);
const Job = mongoose.model('Job', JobSchema);
const Inventory = mongoose.model('Inventory', InventorySchema);
const Customer = mongoose.model('Customer', CustomerSchema);
const Billing = mongoose.model('Billing', BillingSchema);

module.exports = {
  connectMongoDB,
  Booking,
  Job,
  Inventory,
  Customer,
  Billing
};
