export type Role = "user" | "admin";

export interface User { id: number; email: string; role: Role }
export interface TokenResponse { access_token: string; token_type: string; user: User }

export interface Vehicle {
  id: number;
  make: string;
  model: string;
  category: string;
  price: number;
  quantity: number;
  reserved: number;
  available: number;
  year: number | null;
  color: string | null;
}

export type VehicleInput = Omit<Vehicle, "id" | "reserved" | "available">;

export interface Hold { id: number; vehicle_id: number; status: string; created_at: string; expires_at: string }

export interface Order {
  id: number;
  vehicle_id: number | null;
  vehicle_label: string;
  category: string | null;
  color: string | null;
  price: number;
  from_hold: boolean;
  created_at: string;
}

export interface InventoryEvent {
  id: number;
  type: string;
  vehicle_id: number | null;
  vehicle_label: string | null;
  user_email: string | null;
  delta: number;
  amount: number | null;
  detail: string | null;
  created_at: string;
}

export interface Analytics {
  vehicle_count: number;
  units_in_stock: number;
  units_reserved: number;
  inventory_value: number;
  units_sold: number;
  revenue: number;
  by_category: { category: string; units: number; value: number }[];
  purchases_by_day: { date: string; purchases: number; revenue: number }[];
  low_stock: { id: number; label: string; available: number }[];
}

export interface Filters {
  q: string;
  category: string;
  minPrice: string;
  maxPrice: string;
  inStock: boolean;
  sort: "newest" | "price_asc" | "price_desc" | "name";
}
