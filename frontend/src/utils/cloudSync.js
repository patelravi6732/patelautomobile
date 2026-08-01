import axios from 'axios';

const MASTER_BIN_URL = 'https://api.restful-api.dev/objects/ff8081819f7e10ae019fbcb185ca5b9e';

async function fetchMasterStore() {
  try {
    const res = await axios.get(MASTER_BIN_URL);
    if (res.data && res.data.data) {
      return {
        bookings: Array.isArray(res.data.data.bookings) ? res.data.data.bookings : [],
        messages: Array.isArray(res.data.data.messages) ? res.data.data.messages : [],
        jobs: Array.isArray(res.data.data.jobs) ? res.data.data.jobs : []
      };
    }
    return { bookings: [], messages: [], jobs: [] };
  } catch (err) {
    console.warn('Failed to fetch Master Cloud Store:', err);
    return { bookings: [], messages: [], jobs: [] };
  }
}

async function saveMasterStore(storeData) {
  try {
    await axios.put(MASTER_BIN_URL, {
      name: 'PatelAutomobilesMasterBin',
      data: storeData
    });
  } catch (err) {
    console.warn('Failed to save Master Cloud Store:', err);
  }
}

// ---------------- BOOKINGS ----------------
export async function fetchCloudBookings() {
  const store = await fetchMasterStore();
  return store.bookings;
}

export async function pushCloudBooking(newBooking) {
  const store = await fetchMasterStore();
  const exists = store.bookings.some(b => 
    b.id === newBooking.id || 
    (b.vehicle_number === newBooking.vehicle_number && b.preferred_date === newBooking.preferred_date)
  );

  let updatedBookings = store.bookings;
  if (!exists) {
    updatedBookings = [newBooking, ...store.bookings];
  } else {
    updatedBookings = store.bookings.map(b => 
      (b.id === newBooking.id || (b.vehicle_number === newBooking.vehicle_number && b.preferred_date === newBooking.preferred_date))
        ? { ...b, ...newBooking }
        : b
    );
  }

  await saveMasterStore({ ...store, bookings: updatedBookings });
}

export async function updateCloudBookingStatus(bookingId, newStatus) {
  const store = await fetchMasterStore();
  const updatedBookings = store.bookings.map(b => {
    if (b.id === bookingId || String(b.id) === String(bookingId)) {
      return { ...b, status: newStatus };
    }
    return b;
  });
  await saveMasterStore({ ...store, bookings: updatedBookings });
}

// ---------------- MESSAGES (CONTACT INQUIRIES) ----------------
export async function fetchCloudMessages() {
  const store = await fetchMasterStore();
  return store.messages;
}

export async function pushCloudMessage(newMsg) {
  const store = await fetchMasterStore();
  const exists = store.messages.some(m => m.id === newMsg.id || (m.name === newMsg.name && m.phone === newMsg.phone && m.message === newMsg.message));
  
  let updated = store.messages;
  if (!exists) {
    updated = [newMsg, ...store.messages];
  }
  await saveMasterStore({ ...store, messages: updated });
}

// ---------------- WORKSHOP JOBS (CONVERT TO SERVICE) ----------------
export async function fetchCloudJobs() {
  const store = await fetchMasterStore();
  return store.jobs;
}

export async function pushCloudJob(newJob) {
  const store = await fetchMasterStore();
  const exists = store.jobs.some(j => j.id === newJob.id || (j.vehicle_number === newJob.vehicle_number && j.status === 'IN_PROGRESS'));
  let updated = store.jobs;
  if (!exists) {
    updated = [newJob, ...store.jobs];
  }
  await saveMasterStore({ ...store, jobs: updated });
}
