import axios from 'axios';

const MASTER_BIN_URL = 'https://api.restful-api.dev/objects/ff8081819f7e10ae019fbcb185ca5b9e';

/**
 * Fetches all global bookings submitted from ANY mobile, browser, or device.
 */
export async function fetchCloudBookings() {
  try {
    const res = await axios.get(MASTER_BIN_URL);
    if (res.data && res.data.data && Array.isArray(res.data.data.bookings)) {
      return res.data.data.bookings;
    }
    return [];
  } catch (err) {
    console.warn('Failed to fetch Cloud Sync bookings:', err);
    return [];
  }
}

/**
 * Pushes a new booking to Global Cloud Sync so it immediately appears in Admin Dashboard from ANY device.
 */
export async function pushCloudBooking(newBooking) {
  try {
    const existing = await fetchCloudBookings();
    
    // Check duplicate
    const exists = existing.some(b => 
      b.id === newBooking.id || 
      (b.vehicle_number === newBooking.vehicle_number && b.preferred_date === newBooking.preferred_date)
    );

    let updatedBookings = existing;
    if (!exists) {
      updatedBookings = [newBooking, ...existing];
    } else {
      updatedBookings = existing.map(b => 
        (b.id === newBooking.id || (b.vehicle_number === newBooking.vehicle_number && b.preferred_date === newBooking.preferred_date))
          ? { ...b, ...newBooking }
          : b
      );
    }

    await axios.put(MASTER_BIN_URL, {
      name: 'PatelAutomobilesMasterBin',
      data: {
        bookings: updatedBookings
      }
    });

    console.log('Successfully synced booking to Global Master Cloud Store');
  } catch (err) {
    console.warn('Failed to push booking to Global Cloud Store:', err);
  }
}

/**
 * Updates status of a booking in global cloud store (e.g., ACCEPTED or REJECTED)
 */
export async function updateCloudBookingStatus(bookingId, newStatus) {
  try {
    const existing = await fetchCloudBookings();
    const updatedBookings = existing.map(b => {
      if (b.id === bookingId || String(b.id) === String(bookingId)) {
        return { ...b, status: newStatus };
      }
      return b;
    });

    await axios.put(MASTER_BIN_URL, {
      name: 'PatelAutomobilesMasterBin',
      data: {
        bookings: updatedBookings
      }
    });
  } catch (err) {
    console.warn('Failed to update Cloud Sync status:', err);
  }
}
