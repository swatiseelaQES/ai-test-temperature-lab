# Requirement: Create Booking

As a hotel booking user, I want to create a booking so that I can reserve a room.

## Acceptance Criteria

1. A booking can be created with valid guest details, booking dates, deposit status, and additional needs.
2. The API should return a `200` status code for a successful booking.
3. The response should include a `bookingid` and a nested `booking` object.
4. The returned booking object should match the submitted guest details.
5. The system should reject invalid booking data where required fields are missing.
6. The system should reject invalid date ranges where checkout is before checkin.

## Notes

The API under test is based on the public Restful Booker style API.
