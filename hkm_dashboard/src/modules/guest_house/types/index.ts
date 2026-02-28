// Types for Guest House Management

export interface RoomBooking {
  booking_id: string;
  guest_name: string;
  check_in_date: string;
  check_out_date: string;
  check_in_time: string;
  check_out_time: string;
  booking_status: string;
  actual_check_in: string | null;
  actual_check_out: string | null;
  amount: number;
  total_person: number;
  guest_type: string;
  devotee: string | null;
}

export interface Room {
  room_id: string;
  room_details: string;
  floor: string;
  room_type?: string;
  status?: 'booked' | 'available' | 'checking_out_today' | 'checking_in_today';
  is_available?: boolean;
  is_ready_to_book?: boolean;
  booking?: RoomBooking | null;
  availability_note?: string;
  available_from_date?: string | null;
  available_to_date?: string | null;
}

export interface Floor {
  floor: string;
  rooms: Room[];
}

export interface RoomAvailabilitySummary {
  total_rooms: number;
  available_rooms: number;
  booked_rooms: number;
  checking_out_today: number;
  checking_in_today: number;
}

export interface RoomsFloorWiseResponse {
  status: 'success' | 'error';
  date: string;
  floors: Floor[];
  summary: RoomAvailabilitySummary;
  message?: string;
}

