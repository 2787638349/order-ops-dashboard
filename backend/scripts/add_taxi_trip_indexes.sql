ALTER TABLE taxi_trips
  ADD INDEX idx_taxi_trip_distance (trip_distance),
  ADD INDEX idx_taxi_trip_normal_pickup_distance (is_abnormal, pickup_time, trip_distance),
  ADD INDEX idx_taxi_trip_normal_distance_pickup (is_abnormal, trip_distance, pickup_time),
  ADD INDEX idx_taxi_trip_payment_pickup (payment_type, pickup_time),
  ADD INDEX idx_taxi_trip_passenger_pickup (passenger_count, pickup_time),
  ADD INDEX idx_taxi_trip_pickup_location_time (pickup_location_id, pickup_time),
  ADD INDEX idx_taxi_trip_dropoff_location_time (dropoff_location_id, pickup_time);
