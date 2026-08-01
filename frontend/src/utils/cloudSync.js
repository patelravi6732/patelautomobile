import axios from 'axios';

const SYNC_BIN_ID = 'patel_automobile_dandi_bookings_v1';
const CLOUD_API_URL = 'https://api.restful-api.dev/objects';

/**
 * Pushes a booking to Global Cloud Sync so it immediately appears in Admin Dashboard from ANY mobile/browser.
 */
export async function pushCloudBooking(booking) {
  try {
    const payload = {
      name: `PatelBooking_${Date.now()}`,
      data: {
        sync_key: SYNC_BIN_ID,
        booking_id: booking.id || Date.now(),
        customer_name: booking.customer_name,
        mobile_number: booking.mobile_number,
        vehicle_number: booking.vehicle_number,
        bike_model: booking.bike_model || '',
        complaint: booking.complaint || '',
        preferred_date: booking.preferred_date || new Date().toISOString().split('T')[0],
        preferred_time: booking.preferred_time || '10:00 AM',
        status: booking.status || 'PENDING',
        created_at: booking.created_at || new Date().toISOString()
      }
    };
    await axios.post(CLOUD_API_URL, payload);
    console.log('Successfully pushed booking to global Cloud Sync');
  } catch (err) {
    console.warn('Failed to push to Cloud Sync:', err);
  }
}

/**
 * Fetches all bookings submitted across any device/mobile on Vercel or live web.
 */
export async function fetchCloudBookings() {
  try {
    const res = await axios.get(CLOUD_API_URL);
    if (Array.isArray(res.data)) {
      return res.data
        .filter(item => item.data && item.data.sync_key === SYNC_BIN_ID)
        .map(item => ({
          cloud_obj_id: item.id,
          id: item.data.booking_id || item.id,
          customer_name: item.data.customer_name,
          mobile_number: item.data.mobile_number,
          vehicle_number: item.data.vehicle_number,
          bike_model: item.data.bike_model,
          complaint: item.data.complaint,
          preferred_date: item.data.preferred_date,
          preferred_time: item.data.preferred_time,
          status: item.data.status || 'PENDING',
          created_at: item.data.created_at || new Date().toISOString()
        }));
    }
    return [];
  } catch (err) {
    console.warn('Failed to fetch Cloud Sync bookings:', err);
    return [];
  }
}
