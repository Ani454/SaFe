|    | name                                                 | fieldName                       | dataTypeName   | description                                                                                                                                                       |
|---:|:-----------------------------------------------------|:--------------------------------|:---------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|  0 | CaseID                                               | service_request_id              | number         | The unique ID of the service request created.                                                                                                                     |
|  1 | Opened                                               | requested_datetime              | calendar_date  | The date and time when the service request was made                                                                                                               |
|  2 | Closed                                               | closed_date                     | calendar_date  | The date and time when the service request was closed                                                                                                             |
|  3 | Updated                                              | updated_datetime                | calendar_date  | The date and time when the service request was last modified. For requests with status=closed, this will be the date the request was closed                       |
|  4 | Status                                               | status_description              | text           | A single-word indicator of the current state of the service request. (Note: GeoReport V2 only permits ‘open’ and ‘closed’)                                        |
|  5 | Status Notes                                         | status_notes                    | text           | Explanation of why status was changed to current state or more details on current status than conveyed with status alone                                          |
|  6 | Responsible Agency                                   | agency_responsible              | text           | The agency responsible for fulfilling or otherwise addressing the service request.                                                                                |
|  7 | Category                                             | service_name                    | text           | The human readable name of the service request type                                                                                                               |
|  8 | Request Type                                         | service_subtype                 | text           | The human readable name of the service request subtype                                                                                                            |
|  9 | Request Details                                      | service_details                 | text           | The human readable name of the service request details                                                                                                            |
| 10 | Address                                              | address                         | text           | Human readable address or description of location                                                                                                                 |
| 11 | Street                                               | street                          | text           | Primary Street of the associated address. Parks may have a park name instead of a street name. Requests not associated with an address will be blank.             |
| 12 | Supervisor District                                  | supervisor_district             | number         | San Francisco Supervisor District as defined in 'Supervisor Districts as of 2022'                                                                                 |
| 13 | Neighborhood                                         | neighborhoods_sffind_boundaries | text           | San Francisco Neighborhood as defined in 'SF Find Neighborhoods'                                                                                                  |
| 14 | Analysis Neighborhood                                | analysis_neighborhood           | text           | San Francisco Analysis Neighborhood as defined in 'Analysis Neighborhoods'                                                                                        |
| 15 | Police District                                      | police_district                 | text           | San Francisco Police District as defined in 'Current Police Districts'                                                                                            |
| 16 | Latitude                                             | lat                             | number         | Latitude of the location, using the WGS84 projection                                                                                                              |
| 17 | Longitude                                            | long                            | number         | Longitude of the location, using the WGS84 projection                                                                                                             |
| 18 | Point                                                | point                           | point          | Combination of Latitude and Longitude for Socrata native maps                                                                                                     |
| 19 | Point (address)                                      | point_address                   | text           | No description available                                                                                                                                          |
| 20 | Point (city)                                         | point_city                      | text           | No description available                                                                                                                                          |
| 21 | point_geom                                           | point_geom                      | point          | Combination of Latitude and Longitude in Point format                                                                                                             |
| 22 | Point (state)                                        | point_state                     | text           | No description available                                                                                                                                          |
| 23 | Source                                               | source                          | text           | Mechanism or path by which the service request was received; typically ‘Phone’, ‘Text/SMS’, ‘Website’, ‘Mobile App’, ‘Twitter’, etc but terms may vary by system. |
| 24 | Media URL                                            | media_url                       | url            | A URL to media associated with the request, e.g. an image.                                                                                                        |
| 25 | Point (zip)                                          | point_zip                       | text           | No description available                                                                                                                                          |
| 26 | BOS_2012                                             | bos_2012                        | number         | San Francisco Supervisor District as defined in 'Supervisor Districts as of 2012'                                                                                 |
| 27 | data_as_of                                           | data_as_of                      | calendar_date  | Timestamp the row was updated in the source system                                                                                                                |
| 28 | data_loaded_at                                       | data_loaded_at                  | calendar_date  | Timestamp the row was uploaded to the open data portal                                                                                                            |
| 29 | Current Police Districts                             | :@computed_region_qgnn_b9vv     | number         | No description available                                                                                                                                          |
| 30 | Current Supervisor Districts                         | :@computed_region_26cr_cadq     | number         | No description available                                                                                                                                          |
| 31 | Analysis Neighborhoods                               | :@computed_region_ajp5_b2md     | number         | No description available                                                                                                                                          |
| 32 | DELETE - Supervisor Districts                        | :@computed_region_rxqg_mtj9     | number         | No description available                                                                                                                                          |
| 33 | DELETE - Fire Prevention Districts                   | :@computed_region_yftq_j783     | number         | No description available                                                                                                                                          |
| 34 | DELETE - Current Police Districts                    | :@computed_region_jx4q_fizf     | number         | No description available                                                                                                                                          |
| 35 | DELETE - Zip Codes                                   | :@computed_region_bh8s_q3mv     | number         | No description available                                                                                                                                          |
| 36 | DELETE - Police Districts                            | :@computed_region_p5aj_wyqh     | number         | No description available                                                                                                                                          |
| 37 | DELETE - Neighborhoods                               | :@computed_region_fyvs_ahh9     | number         | No description available                                                                                                                                          |
| 38 | DELETE - Neighborhoods_from_fyvs_ahh9                | :@computed_region_f58d_8dbm     | number         | No description available                                                                                                                                          |
| 39 | DELETE - 2017 Fix It Zones                           | :@computed_region_9dfj_4gjx     | number         | No description available                                                                                                                                          |
| 40 | DELETE - SF Find Neighborhoods                       | :@computed_region_vtsz_7cme     | number         | No description available                                                                                                                                          |
| 41 | Civic Center Harm Reduction Project Boundary         | :@computed_region_n4xg_c4py     | number         | No description available                                                                                                                                          |
| 42 | DELETE - Current Supervisor Districts                | :@computed_region_sruu_94in     | number         | No description available                                                                                                                                          |
| 43 | Fix It Zones as of 2017-11-06                        | :@computed_region_4isq_27mq     | number         | No description available                                                                                                                                          |
| 44 | Invest In Neighborhoods (IIN) Areas                  | :@computed_region_viu7_rrfi     | number         | No description available                                                                                                                                          |
| 45 | DELETE - HSOC Zones                                  | :@computed_region_fcz8_est8     | number         | No description available                                                                                                                                          |
| 46 | Fix It Zones as of 2018-02-07                        | :@computed_region_pigm_ib2e     | number         | No description available                                                                                                                                          |
| 47 | CBD, BID and GBD Boundaries as of 2017               | :@computed_region_9jxd_iqea     | number         | No description available                                                                                                                                          |
| 48 | Central Market/Tenderloin Boundary                   | :@computed_region_6ezc_tdp2     | number         | No description available                                                                                                                                          |
| 49 | Areas of Vulnerability, 2016                         | :@computed_region_6pnf_4xz7     | number         | No description available                                                                                                                                          |
| 50 | Central Market/Tenderloin Boundary Polygon - Updated | :@computed_region_h4ep_8xdi     | number         | No description available                                                                                                                                          |
| 51 | HSOC Zones as of 2018-06-05                          | :@computed_region_nqbw_i6c3     | number         | No description available                                                                                                                                          |
| 52 | OWED Public Spaces                                   | :@computed_region_2dwj_jsy4     | number         | No description available                                                                                                                                          |
| 53 | Parks Alliance CPSI (27+TL sites)                    | :@computed_region_y6ts_4iup     | number         | No description available                                                                                                                                          |
| 54 | Neighborhoods                                        | :@computed_region_jwn9_ihcz     | number         | No description available                                                                                                                                          |
| 55 | SF Find Neighborhoods                                | :@computed_region_6qbp_sg9q     | number         | No description available                                                                                                                                          |

# 12 required columns
1. What am I counting or measuring? That tells you which fields hold the measure, such as a date to count by or two dates to subtract.

2. What am I grouping or slicing by? The “by category, agency, neighborhood” part of a question tells you which fields you group on.
3. What do I need to trust the answer? Fields that identify a record or confirm its state, even if they never appear in the final result.

# Problems we are solving

1. Volume opened and closed per day/week, by category, agency, and neighborhood

Data Required :
    1. What am I counting or measuring? That tells you which fields hold the measure, such as a date to count by or two dates to subtract.
        2. Opened - requested_datetime
        3. Closed - closed_date
    2. What am I grouping or slicing by? The “by category, agency, neighborhood” part of a question tells you which fields you group on.
        1. Category - service_name
        2. Request Type - service_subtype
        4. Responsible Agency - agency_responsible 
        5. neighbouhoof - neighborhoods_sffind_boundaries (not using naalysis one as it was created based on population )

    3. What do I need to trust the answer? Fields that identify a record or confirm its state, even if they never appear in the final result.
        1. status_notes
        2. status_description

    Supporting :""
    Not Required: 
    'updated_datetime', ':@computed_region_yftq_j783', '', 'data_loaded_at', 'long', 'source', '', 'police_district', 'street', ':@computed_region_4isq_27mq', 'lat', 'supervisor_district', '', ':@computed_region_pigm_ib2e', 'point', ':@computed_region_jwn9_ihcz', ':@computed_region_vtsz_7cme', '', ':@computed_region_qgnn_b9vv', ':@computed_region_9jxd_iqea', ':@computed_region_2dwj_jsy4', 'data_as_of', ':@computed_region_6ezc_tdp2', ':@computed_region_bh8s_q3mv', ':@computed_region_rxqg_mtj9', 'bos_2012', ':@computed_region_y6ts_4iup', ':@computed_region_nqbw_i6c3', ':@computed_region_6qbp_sg9q', ':@computed_region_9dfj_4gjx', '', 'analysis_neighborhood', '', ':@computed_region_6pnf_4xz7', ':@computed_region_n4xg_c4py', '', 'service_request_id', ':@computed_region_26cr_cadq', 'service_details', 'address', ':@computed_region_fcz8_est8', ':@computed_region_sruu_94in', ':@computed_region_f58d_8dbm', ':@computed_region_p5aj_wyqh', 'media_url', ':@computed_region_h4ep_8xdi', ':@computed_region_ajp5_b2md', ':@computed_region_fyvs_ahh9', ':@computed_region_jx4q_fizf', ':@computed_region_viu7_rrfi', 'point_geom', 'neighborhoods_sffind_boundaries'


2. How long cases take to close, median and p90, by category and neighborhood
    Data Required :
    1. What am I counting or measuring? That tells you which fields hold the measure, such as a date to count by or two dates to subtract.
        2. Opened - requested_datetime
        3. Closed - closed_date
    2. What am I grouping or slicing by? The “by category, agency, neighborhood” part of a question tells you which fields you group on.
        1. Category - service_name
        5. neighbouhood - not able to understand the difference one between the two

    3. What do I need to trust the answer? Fields that identify a record or confirm its state, even if they never appear in the final result.
        1. status_notes
        2. status_description

    Supporting :""
    Not Required: 
    'updated_datetime', ':@computed_region_yftq_j783', '', 'data_loaded_at', 'long', 'source', '', 'police_district', 'street', ':@computed_region_4isq_27mq', 'lat', 'supervisor_district', '', ':@computed_region_pigm_ib2e', 'point', ':@computed_region_jwn9_ihcz', ':@computed_region_vtsz_7cme', 'agency_responsible', ':@computed_region_qgnn_b9vv', ':@computed_region_9jxd_iqea', ':@computed_region_2dwj_jsy4', 'data_as_of', ':@computed_region_6ezc_tdp2', ':@computed_region_bh8s_q3mv', ':@computed_region_rxqg_mtj9', 'bos_2012', ':@computed_region_y6ts_4iup', ':@computed_region_nqbw_i6c3', ':@computed_region_6qbp_sg9q', ':@computed_region_9dfj_4gjx', '', 'analysis_neighborhood', '', ':@computed_region_6pnf_4xz7', ':@computed_region_n4xg_c4py', '', 'service_request_id', ':@computed_region_26cr_cadq', 'service_details', 'address', ':@computed_region_fcz8_est8', ':@computed_region_sruu_94in', ':@computed_region_f58d_8dbm', ':@computed_region_p5aj_wyqh', 'media_url', ':@computed_region_h4ep_8xdi', ':@computed_region_ajp5_b2md', ':@computed_region_fyvs_ahh9', ':@computed_region_jx4q_fizf', ':@computed_region_viu7_rrfi', 'point_geom', 'neighborhoods_sffind_boundaries'

3. Open backlog and aging: what's still open after 30, 60, 90 days
ata Required :
    1. What am I counting or measuring? That tells you which fields hold the measure, such as a date to count by or two dates to subtract.
        2. Opened - requested_datetime
        3. Closed - closed_date
    2. What am I grouping or slicing by? The “by category, agency, neighborhood” part of a question tells you which fields you group on.

    3. What do I need to trust the answer? Fields that identify a record or confirm its state, even if they never appear in the final result.
        1. status_notes
        2. status_description

    Supporting :""
    Not Required: 
    'updated_datetime', ':@computed_region_yftq_j783', '', 'data_loaded_at', 'long', 'source', '', 'police_district', 'street', ':@computed_region_4isq_27mq', 'lat', 'supervisor_district', 'agency_responsible', ':@computed_region_pigm_ib2e', 'point', ':@computed_region_jwn9_ihcz', ':@computed_region_vtsz_7cme', '', ':@computed_region_qgnn_b9vv', ':@computed_region_9jxd_iqea', ':@computed_region_2dwj_jsy4', 'data_as_of', ':@computed_region_6ezc_tdp2', ':@computed_region_bh8s_q3mv', ':@computed_region_rxqg_mtj9', 'bos_2012', ':@computed_region_y6ts_4iup', ':@computed_region_nqbw_i6c3', ':@computed_region_6qbp_sg9q', ':@computed_region_9dfj_4gjx', '', 'analysis_neighborhood', '', ':@computed_region_6pnf_4xz7', ':@computed_region_n4xg_c4py', '', 'service_request_id', ':@computed_region_26cr_cadq', 'service_details', 'address', ':@computed_region_fcz8_est8', ':@computed_region_sruu_94in', ':@computed_region_f58d_8dbm', ':@computed_region_p5aj_wyqh', 'media_url', ':@computed_region_h4ep_8xdi', ':@computed_region_ajp5_b2md', ':@computed_region_fyvs_ahh9', ':@computed_region_jx4q_fizf', ':@computed_region_viu7_rrfi', 'point_geom', 'neighborhoods_sffind_boundaries'
4. Data quality: missing neighborhood, duplicate CaseIDs, cases marked closed with no closed date, status changes that don't make sense
ata Required :
    1. What am I counting or measuring? That tells you which fields hold the measure, such as a date to count by or two dates to subtract.
        1. CaseID - service_request_id
        2. Opened - requested_datetime
        3. Closed - closed_date
        4. Updated- updated_datetime
        5. neighbouhoof - not able to understand the difference one between the two
    2. What am I grouping or slicing by? The “by category, agency, neighborhood” part of a question tells you which fields you group on.

    3. What do I need to trust the answer? Fields that identify a record or confirm its state, even if they never appear in the final result.
        1. status_notes
        2. status_description - only shows either opened/closed (not sure about where to check history for the same)

    Supporting :""
    Not Required: 
    'updated_datetime', ':@computed_region_yftq_j783', '', 'data_loaded_at', 'long', 'source', '', 'police_district', 'street', ':@computed_region_4isq_27mq', 'lat', 'supervisor_district', 'agency_responsible', ':@computed_region_pigm_ib2e', 'point', ':@computed_region_jwn9_ihcz', ':@computed_region_vtsz_7cme', '', ':@computed_region_qgnn_b9vv', ':@computed_region_9jxd_iqea', ':@computed_region_2dwj_jsy4', 'data_as_of', ':@computed_region_6ezc_tdp2', ':@computed_region_bh8s_q3mv', ':@computed_region_rxqg_mtj9', 'bos_2012', ':@computed_region_y6ts_4iup', ':@computed_region_nqbw_i6c3', ':@computed_region_6qbp_sg9q', ':@computed_region_9dfj_4gjx', '', 'analysis_neighborhood', '', ':@computed_region_6pnf_4xz7', ':@computed_region_n4xg_c4py', '', 'service_request_id', ':@computed_region_26cr_cadq', 'service_details', 'address', ':@computed_region_fcz8_est8', ':@computed_region_sruu_94in', ':@computed_region_f58d_8dbm', ':@computed_region_p5aj_wyqh', 'media_url', ':@computed_region_h4ep_8xdi', ':@computed_region_ajp5_b2md', ':@computed_region_fyvs_ahh9', ':@computed_region_jx4q_fizf', ':@computed_region_viu7_rrfi', 'point_geom', 'neighborhoods_sffind_boundaries'

# Data related to service details and servise_subtypes

1. this what i observed - service details is not always included, meaning it has no value so its completly discarded from the results. So I will be filtering with only subtypes

import requests

url='https://data.sf.gov/resource/vw6y-z8j6.json'

import requests

url='https://data.sf.gov/resource/vw6y-z8j6.json'

response = requests.get(url)
print(response.status_code)
records=response.json()
print(type(records), len(records))

sd_set = set()
service_subtype_set = set()
service_subtype_list = []
sd_list = []


for record in records:
    #print(record.get('service_details', 'No service details available'))
    sd_set.add(record.get('service_details', 'No service details available'))
    service_subtype_set.add(record.get('service_subtype', 'No service subtype available'))
    service_subtype_list.append(record.get('service_subtype',"No service subtype available"))
    sd_list.append(record.get('service_details',"No service details available"))

print(f"Unique service details: {len(sd_set)}, Unique service subtypes: {len(service_subtype_set)}, Total service subtypes: {len(service_subtype_list)}, Total service details: {len(sd_list)}")
#print(f"sd list:{sd_list}, service subtype list: {service_subtype_list}")

diff=0
diff2=0

for i in range(len(sd_list)):
    if sd_list[i] == "No service details available":
        diff+=1
    if service_subtype_list[i] == "No service subtype available":
        diff2+=1

print(diff)
print(diff2)

Results : 200
<class 'list'> 1000
Unique service details: 239, Unique service subtypes: 119, Total service subtypes: 1000, Total service details: 1000
18
0

# I am not sure about adding supervisor distict to plans 12 fields which I am mapping, 