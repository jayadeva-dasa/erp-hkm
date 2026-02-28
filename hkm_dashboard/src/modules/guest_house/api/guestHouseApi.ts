// API functions for Guest House Management
import apiClient from '../../../services/apiClient';
import { RoomsFloorWiseResponse } from '../types';

/**
 * Get rooms grouped by floor for a specific date
 * @param date - Date in YYYY-MM-DD format (optional, defaults to today)
 * @returns Promise with rooms data grouped by floor
 */
export const getRoomsFloorWise = async (date?: string): Promise<RoomsFloorWiseResponse> => {
  try {
    const params: any = {};
    if (date) {
      params.date = date;
    }

    const response = await apiClient.get(
      '/api/method/hkm.api.v1.guest_house.get_rooms_floor_wise',
      { params }
    );

    const result = response.data.message || response.data;

    if (result.status === 'success') {
      return result;
    }

    throw new Error(result.message || 'Failed to fetch room availability');
  } catch (error: any) {
    console.error('Error fetching room availability:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to fetch room availability'
    );
  }
};

/**
 * Get available rooms for a date range
 */
export const getAvailableRooms = async (fromDate: string, toDate: string) => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.v1.guest_house.get_available_rooms',
      { params: { from_date: fromDate, to_date: toDate } }
    );

    const result = response.data.message || response.data;

    if (result.status === 'success') {
      return result;
    }

    throw new Error(result.message || 'Failed to fetch available rooms');
  } catch (error: any) {
    console.error('Error fetching available rooms:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to fetch available rooms'
    );
  }
};

/**
 * Search devotees
 */
export const searchDevotees = async (searchTerm?: string, requiredAll: boolean = false) => {
  try {
    const params: any = {};
    if (searchTerm) {
      params.search_term = searchTerm;
    }
    if (requiredAll) {
      params.required_all = true;
    }

    const response = await apiClient.get(
      '/api/method/hkm.api.v1.guest_house.get_devotees_search',
      { params }
    );

    return response.data.message || response.data;
  } catch (error: any) {
    console.error('Error searching devotees:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to search devotees'
    );
  }
};

/**
 * Get room types
 */
export const getRoomTypes = async () => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.v1.guest_house.get_room_types'
    );

    return response.data.message || response.data;
  } catch (error: any) {
    console.error('Error fetching room types:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to fetch room types'
    );
  }
};

/**
 * Create a new booking
 */
export interface BookingRoomDetail {
  room: string;
  amount: number;
}

export interface CreateBookingData {
  from_date: string;
  to_date: string;
  full_name: string;
  address: string;
  total_person: number;
  guest_type: string;
  devotee?: string;
  amount?: number;
  room_details: BookingRoomDetail[];
}

export const createBooking = async (bookingData: CreateBookingData): Promise<string> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.v1.guest_house.create_booking',
      bookingData
    );

    const result = response.data.message || response.data;
    return result;
  } catch (error: any) {
    console.error('Error creating booking:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to create booking'
    );
  }
};

/**
 * Upload images for a booking
 */
export const uploadBookingImages = async (bookingId: string, images: File[]): Promise<any> => {
  try {
    const formData = new FormData();
    images.forEach((image) => {
      formData.append('image', image);
    });

    const response = await apiClient.post(
      `/api/method/hkm.api.v1.guest_house.upload_booking_images?booking_id=${bookingId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    const result = response.data.message || response.data;

    if (result.status === 'success') {
      return result;
    }

    throw new Error(result.message || 'Failed to upload images');
  } catch (error: any) {
    console.error('Error uploading booking images:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to upload images'
    );
  }
};

/**
 * Search bookings with filters
 */
export interface SearchBookingsParams {
  page?: number;
  page_size?: number;
  search_field?: string;
  search_text?: string;
  from_date?: string;
  to_date?: string;
  devotee?: string[];
  sort_field?: string;
  sort_order?: 'asc' | 'desc';
}

export const searchBookings = async (params: SearchBookingsParams) => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.v1.guest_house.search_bookings',
      params
    );

    return response.data.message || response.data;
  } catch (error: any) {
    console.error('Error searching bookings:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to search bookings'
    );
  }
};

/**
 * Get detailed booking information
 */
export const getBookingDetailedInfo = async (bookingId: string) => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.v1.guest_house.get_booking_detailed_info',
      { params: { booking_id: bookingId } }
    );

    return response.data.message || response.data;
  } catch (error: any) {
    console.error('Error fetching booking details:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to fetch booking details'
    );
  }
};

/**
 * Cancel a booking
 */
export const cancelBooking = async (bookingId: string) => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.v1.guest_house.cancel_booking',
      { booking_id: bookingId }
    );

    return response.data.message || response.data;
  } catch (error: any) {
    console.error('Error canceling booking:', error);
    throw new Error(
      error.response?.data?.exception ||
      error.response?.data?.message ||
      error.message ||
      'Failed to cancel booking'
    );
  }
};

export const guestHouseApi = {
  getRoomsFloorWise,
  getAvailableRooms,
  searchDevotees,
  getRoomTypes,
  createBooking,
  uploadBookingImages,
  searchBookings,
  getBookingDetailedInfo,
  cancelBooking,
};

