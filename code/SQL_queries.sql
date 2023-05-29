-- Query 1: find the staff members working on 10.5.21: ssNo, role, vaccination status, location

SELECT sm.ssno, sm.name, sm.phone, sm.role, sm.status, v.location
FROM staffmembers sm
         JOIN shifts s
              ON sm.ssno = s.worker
         JOIN vaccinations v
              ON v.location = s.station
WHERE s.weekday = 'Monday'
  AND v.date = '2021-05-10';

-- Query 2: list all the doctors working on Wed in Helsinki

SELECT ssNo, staffmembers.name
FROM StaffMembers, Shifts, Vaccinationstations
    WHERE shifts.weekday = 'Wednesday'
    AND staffmembers.role = 'doctor'
    AND Shifts.worker = StaffMembers.ssNo
    AND staffmembers.hospital = vaccinationstations.name
    AND address LIKE '%HELSINKI';

-- Query 3: list batchID and phone number of hospitals where batches with inconsistent location data should be

SELECT tl.batchid, vb.location AS current_location, tl.arrival AS last_location
FROM (SELECT tl.batchid, MAX(tl.datearr) AS last_date
      FROM transportationlog tl
      GROUP BY tl.batchid) bld
         JOIN transportationlog tl
              ON tl.batchid = bld.batchid
                  AND tl.datearr = bld.last_date
         JOIN vaccinebatch vb
              ON tl.batchid = vb.batchid;

SELECT vaccinebatch.batchid, vaccinationstations.phone
FROM vaccinebatch, vaccinationstations,
(SELECT transportationlog.batchid AS batchid, transportationlog.arrival AS arrival
FROM transportationlog,
(SELECT transportationlog.batchID, MAX(datearr)
    FROM transportationlog GROUP BY batchID) AS latestarrival
    WHERE transportationlog.batchid = latestarrival.batchid
	AND transportationlog.datearr = latestarrival.max) AS latestlocation
WHERE latestlocation.batchid = vaccinebatch.batchid
AND vaccinebatch.location <> latestlocation.arrival
AND vaccinationstations.name = latestlocation.arrival;

-- Query 4: all patients with critical symptoms diagnosed after 10.5.21 matched with vaccination data

SELECT diagnosis.patient AS patient, vaccinebatch.batchID AS batchID,
    vaccinetype.name AS vaccineType, vaccinations.date AS date,
    vaccinations.location AS location
FROM vaccinebatch, diagnosis, vaccinetype, vaccinations, symptoms, vaccinepatients, manufacturer
    WHERE symptoms.criticality = 1
    AND diagnosis.symptom = symptoms.name
    AND diagnosis.date > '2021-05-10'
    AND diagnosis.patient = vaccinepatients.patientssno
    AND vaccinations.batchID = vaccinebatch.batchid
    AND vaccinebatch.manufacturer = manufacturer
    AND vaccinepatients.location = vaccinations.location
    AND vaccinepatients.date = vaccinations.date;

-- Query 5: create a view for patients with additional column vaccinationStatus (0/1)
CREATE OR REPLACE VIEW VaccinatedPatients AS
SELECT p.*,
       CASE
           WHEN doses_took >= 2 THEN 1
           ELSE 0
           END AS vaccinationStatus
FROM (SELECT patientssno, COUNT(*) AS doses_took
      FROM vaccinepatients
      GROUP BY patientssno) pdt
         JOIN patients p
              ON p.ssno = pdt.patientssno;

-- Query 6: find the total amount of vaccine doses in every clinic, as well as amounts of doses by vaccine type

SELECT sub.location,
       sub.vaccine,
       sub.amount,
       SUM(sub.amount) OVER (PARTITION BY sub.location) AS totalamount
FROM (SELECT location, mf.vaccine, SUM(amount) AS amount
      FROM vaccinebatch vb
               JOIN manufacturer mf
                    ON vb.manufacturer = mf.id
      GROUP BY location, mf.vaccine
      ORDER BY location, mf.vaccine) sub;

-- Query 7:
-- For each vaccine type, you should find the average frequency of different symptoms diagnosed.
-- The symptom should not be considered to be caused by the vaccine, if it has been diagnosed
-- before the patient got the vaccine. If a patient has received two different types of vaccines
-- before the diagnosis of the symptom, the symptom should be counted once for both of the vaccines.

WITH symptom_cases_by_type AS (WITH symptom_report AS (SELECT DISTINCT vp.patientssno,
                                                                       d.symptom,
                                                                       d.date  AS recorded_date,
                                                                       vp.date AS vaccination_date,
                                                                       vp.location
                                                       FROM diagnosis d
                                                                JOIN vaccinepatients vp
                                                                     ON d.date >= vp.date
                                                                         AND d.patient = vp.patientssno
                                                                JOIN vaccinatedpatients vdp
                                                                     ON vdp.ssno = vp.patientssno
                                                       WHERE vdp.vaccinationStatus = 0
                                                       UNION
                                                       SELECT *
                                                       FROM (SELECT DISTINCT vp.patientssno,
                                                                             d.symptom,
                                                                             d.date                                          AS recorded_date,
                                                                             MAX(vp.date) OVER (PARTITION BY vp.patientssno) AS vaccination_date,
                                                                             vp.location
                                                             FROM diagnosis d
                                                                      JOIN vaccinepatients vp
                                                                           ON d.patient = vp.patientssno
                                                                      JOIN vaccinatedpatients vdp
                                                                           ON vdp.ssno = vp.patientssno
                                                             WHERE vdp.vaccinationStatus = 1) dvv
                                                       WHERE dvv.recorded_date >= dvv.vaccination_date),
                                    vaccine_type_used AS (SELECT DISTINCT vp.date, vp.location, mf.vaccine
                                                          FROM vaccinepatients vp
                                                                   JOIN vaccinations v
                                                                        ON v.date = vp.date
                                                                            AND v.location = vp.location
                                                                   JOIN vaccinebatch vb
                                                                        ON vb.batchid = v.batchid
                                                                   JOIN manufacturer mf
                                                                        ON mf.id = vb.manufacturer)
                               SELECT vtu.vaccine, sr.symptom, COUNT(*) AS number_of_cases
                               FROM symptom_report sr
                                        JOIN vaccine_type_used vtu
                                             ON sr.vaccination_date = vtu.date
                                                 AND sr.location = vtu.location
                               GROUP BY vtu.vaccine, sr.symptom),
     total_cases AS (WITH vaccine_type_used AS (SELECT DISTINCT vp.date, vp.location, mf.vaccine
                                                FROM vaccinepatients vp
                                                         JOIN vaccinations v
                                                              ON v.date = vp.date
                                                                  AND v.location = vp.location
                                                         JOIN vaccinebatch vb
                                                              ON vb.batchid = v.batchid
                                                         JOIN manufacturer mf
                                                              ON mf.id = vb.manufacturer)
                     SELECT vtu.vaccine, COUNT(*) AS total_patients
                     FROM vaccine_type_used vtu
                              JOIN vaccinepatients vp
                                   ON vtu.location = vp.location
                                       AND vtu.date = vp.date
                     GROUP BY vtu.vaccine)
SELECT scbt.vaccine, scbt.symptom, (number_of_cases::REAL / total_patients::REAL) AS frequency
FROM symptom_cases_by_type scbt
         JOIN total_cases tc
              ON scbt.vaccine = tc.vaccine;
