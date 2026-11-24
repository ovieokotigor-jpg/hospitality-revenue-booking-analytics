# Data dictionary

All records are synthetic. NGN values exclude tax. Dates are local calendar dates. Blank cells mean NULL, not zero. One booking reserves one room.

## hotels

| Column | Definition |
|---|---|
| `hotel_id` | INTEGER primary key |
| `hotel_name` | Fictional property name |
| `market` | Business or Leisure positioning |
| `city` | Nigerian city, no actual address |
| `physical_rooms` | Total rooms before out-of-service deductions |
| `base_rate_ngn` | Starting reference nightly rate, NGN excluding taxes |

## guests

| Column | Definition |
|---|---|
| `guest_id` | INTEGER primary key; synthetic customer, no PII |
| `segment` | Business, Leisure or Group; fixed customer segment |
| `home_region` | Domestic or International; fictional classification |

## channels

| Column | Definition |
|---|---|
| `channel_id` | INTEGER primary key |
| `channel_name` | Direct, OTA or Corporate agent |
| `commission_rate` | Fraction of realized room revenue charged as commission |

## inventory

| Column | Definition |
|---|---|
| `inventory_id` | INTEGER primary key |
| `hotel_id` | FK to hotels |
| `stay_date` | ISO date; one hotel-day |
| `rooms_available` | Sellable rooms after out-of-service deductions |
| `out_of_service_rooms` | Physical rooms unavailable for sale |

## bookings

| Column | Definition |
|---|---|
| `booking_id` | INTEGER key; 150 identical raw copies repeat this key |
| `hotel_id` | FK to hotels; 15 deliberately invalid raw references |
| `guest_id` | FK to guests |
| `channel_id` | FK to channels |
| `booking_date` | ISO reservation creation date; can be in 2023 for early 2024 arrivals |
| `arrival_date` | ISO date, except 200 deliberately DD/MM/YYYY source dates |
| `departure_date` | ISO checkout date, exclusive last night |
| `cancel_date` | ISO cancellation date, blank for completed stays |
| `status` | Completed or Cancelled; 300 raw values padded/lowercase |
| `lead_days` | Days from booking to arrival, 1–180 |
| `nights` | Booked length of stay, 1–6 nights; one room per booking |
| `quoted_adr_ngn` | Agreed nightly room rate NGN, constant across this booking; 25 negative source errors |
| `nightly_service_cost_ngn` | Variable servicing cost per occupied night; not full hotel cost |
| `special_requests` | Requested amenity category; 250 missing entries become Unknown |
| `satisfaction_score` | 1–5 survey rating, optional and completed-stay only |

## booking_nights

| Column | Definition |
|---|---|
| `booking_night_id` | INTEGER primary key |
| `booking_id` | FK to bookings |
| `stay_date` | ISO booked night, including cancelled reservations; occupancy depends on booking status |

## Derived measures

`booking_mart` retains cleaned booking fields and joins hotel_name, market, guest segment, channel_name and commission_rate. `is_cancelled` is 1 for cancellation, else 0. `quoted_value_ngn` = nights × quoted ADR. This is booked value, not earned revenue. `realized_room_revenue_ngn` is zero for cancellations and quoted value for completed stays. `commission_ngn` is realized revenue × commission rate. `service_cost_ngn` is completed room-nights × nightly service cost. `contribution_ngn` = realized revenue − commission − service cost, before fixed costs, tax and capital costs.

`daily_hotel` is a complete inventory grid, including dates with no occupied rooms. It has hotel_id, stay_date, rooms_available, out_of_service_rooms, occupied_rooms (completed booking nights), room_revenue_ngn and contribution_ngn. Zero occupied rooms is valid; bookings with source errors are excluded, so occupancy is based on valid retained records and may undercount true occupancy. ADR = room revenue / occupied room-nights. RevPAR = room revenue / available room-nights. Occupancy = occupied / available room-nights. All aggregate ratios use sums, not averages of hotel percentages.

`quarantine` contains original normalized booking columns plus reason. `bookings_normalized` retains deduplicated and standardized raw records. `booking_nights` is cleaned by excluding children of quarantined bookings. Survey scores are not imputed and response coverage is reported separately. Events after 2025 are not needed: all stays end by 31 December 2025.
