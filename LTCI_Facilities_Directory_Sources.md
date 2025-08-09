# South Korea LTCI Facilities Directory & Data Sources

## Official Facility Directory Sources

### 1. National Health Insurance Service - Long-Term Care Facility Search
- **Website**: https://www.longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650
- **Description**: Official LTCI facility search portal by NHIS
- **Data Available**: 
  - Facility names, addresses, contact information
  - Service types and capacity
  - Facility ratings (A-E grade system)
  - Insurance coverage details
- **Update Frequency**: Real-time
- **Access Method**: Web interface (no direct API)
- **Languages**: Korean

### 2. Health Insurance Review & Assessment Service (HIRA)
- **Website**: https://biz.hira.or.kr/
- **Portal**: https://www.konect.or.kr/en/
- **Description**: Claims data and facility information
- **Data Available**:
  - Healthcare provider directory
  - Claims statistics
  - Quality assessments
- **Update Frequency**: Monthly
- **Access Method**: Web portal, data request system

### 3. Ministry of Health and Welfare
- **Website**: https://www.mohw.go.kr/eng/
- **Statistics Portal**: Various departmental reports
- **Description**: Policy documents and statistical reports
- **Data Available**:
  - Annual budget allocations
  - Policy changes and updates
  - Demographic statistics
- **Update Frequency**: Annual/Quarterly
- **Access Method**: Document downloads

## Facility Types in Directory

### Institutional Care Facilities
1. **요양시설 (Nursing Homes)**
   - Long-term residential care
   - 24-hour professional care
   - Medical supervision

2. **요양병원 (Long-term Care Hospitals)**
   - Medical treatment focus
   - Physician-supervised care
   - Therapeutic services

3. **노인요양공동생활가정 (Elderly Care Group Homes)**
   - Small-scale residential care
   - Home-like environment
   - 5-9 residents typically

### Community Care Services
1. **주야간보호 (Day & Night Care Centers)**
   - Daily activity programs
   - Respite care services
   - Transportation included

2. **단기보호 (Short-term Care)**
   - Temporary residential care
   - Respite for family caregivers
   - Emergency care services

### Home-Based Services
1. **방문요양 (Visiting Care Services)**
   - Personal care assistance
   - Daily living support
   - Household help

2. **방문목욕 (Visiting Bathing Services)**
   - Professional bathing assistance
   - Specialized equipment
   - Hygiene support

3. **방문간호 (Visiting Nursing Services)**
   - Medical care at home
   - Medication management
   - Health monitoring

## Data Access and Download Methods

### Direct Access Portals

#### 1. LTCI Facility Search System
- **URL**: https://www.longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650
- **Search Parameters**:
  - Region (시/도/군/구)
  - Service Type
  - Facility Rating
  - Availability Status
- **Data Format**: HTML/Web interface
- **Scraping Considerations**: 
  - Requires session management
  - Search-based data retrieval
  - Rate limiting may apply

#### 2. NHIS Data Service
- **URL**: http://nhiss.nhis.or.kr
- **Access Type**: Registered researcher access only
- **Requirements**:
  - Research proposal submission
  - Institutional ethics approval
  - NHIS review committee approval
- **Data Format**: Customized datasets
- **Timeline**: 2-3 months approval process

#### 3. HIRA Business Intelligence Portal
- **URL**: https://biz.hira.or.kr/
- **Access Type**: Healthcare provider and researcher access
- **Data Available**:
  - Provider directories
  - Claims statistics
  - Quality metrics
- **Format**: Web portal with download options

### Alternative Data Sources

#### 1. Statistics Korea (KOSTAT)
- **Website**: https://kostat.go.kr/
- **English**: https://kostat.go.kr/portal/eng/
- **Data**: Demographic and healthcare statistics
- **Format**: Excel, CSV downloads available

#### 2. Korea Health Industry Development Institute (KHIDI)
- **Website**: https://www.khidi.or.kr/
- **Data**: Healthcare industry statistics and analysis
- **Access**: Public reports and data downloads

#### 3. Local Government Portals
- **Seoul**: https://data.seoul.go.kr/
- **Busan**: https://data.busan.go.kr/
- **Other Cities**: Various municipal data portals
- **Data**: Regional facility information and statistics

## Web Scraping and API Considerations

### Technical Requirements

#### 1. LTCI Portal Scraping
```python
# Example scraping parameters
base_url = "https://www.longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web"
parameters = {
    'menuId': 'npe0000000650',
    'searchType': 'region',
    'region_code': '11',  # Seoul
    'service_type': 'all'
}
```

#### 2. Rate Limiting Guidelines
- **Recommended Delay**: 2-5 seconds between requests
- **Session Management**: Required for most portals
- **Headers**: User-Agent rotation recommended
- **Respect robots.txt**: Check site policies

#### 3. Data Structure
```json
{
  "facility_id": "unique_identifier",
  "name": "facility_name",
  "address": "full_address",
  "contact": {
    "phone": "phone_number",
    "fax": "fax_number"
  },
  "services": ["service_type1", "service_type2"],
  "capacity": "number_of_beds",
  "rating": "A-E_grade",
  "coordinates": {
    "latitude": "lat_value",
    "longitude": "lng_value"
  }
}
```

### Legal and Ethical Considerations

#### 1. Data Usage Rights
- Personal information protection laws apply
- Commercial use may require permissions
- Attribution requirements for public data

#### 2. Access Compliance
- Follow terms of service for each portal
- Respect rate limits and server capacity
- Consider data minimization principles

#### 3. Privacy Protection
- Remove or mask personal identifiers
- Aggregate data when possible
- Secure data storage and transmission

## Update Automation Strategies

### 1. Scheduled Data Collection
- **Frequency**: Weekly for facility directory
- **Timing**: Off-peak hours (2-6 AM KST)
- **Scope**: Incremental updates only

### 2. Change Detection
- **Method**: Hash comparison of facility records
- **Alerts**: Notify on new facilities or major changes
- **Validation**: Cross-reference with multiple sources

### 3. Data Quality Monitoring
- **Completeness**: Check for missing required fields
- **Accuracy**: Validate against known benchmarks
- **Consistency**: Compare across different sources

## Integration APIs and Services

### Currently Available APIs

#### 1. Government Open Data APIs
- **Portal**: https://www.data.go.kr/
- **LTCI Data**: Limited availability
- **Format**: REST API, JSON/XML
- **Authentication**: API key required

#### 2. Healthcare Information APIs
- **Provider**: Various private companies
- **Coverage**: Facility directories and ratings
- **Cost**: Subscription-based
- **Reliability**: Varies by provider

### Future API Development Opportunities

#### 1. Official NHIS API
- **Status**: Not currently available for public use
- **Potential**: High-value comprehensive data
- **Timeline**: Unknown

#### 2. Third-party Aggregators
- **Market Gap**: Comprehensive facility API service
- **Business Opportunity**: Data aggregation and standardization
- **Value Proposition**: Real-time updates and analytics

## Data Maintenance Checklist

### Daily Tasks
- [ ] Monitor scraping processes for errors
- [ ] Check data pipeline health
- [ ] Validate critical data points

### Weekly Tasks
- [ ] Update facility directory
- [ ] Quality check new or changed records
- [ ] Backup data and configurations

### Monthly Tasks
- [ ] Full data validation against source systems
- [ ] Performance optimization review
- [ ] Update documentation and processes

### Quarterly Tasks
- [ ] Review data sources for changes
- [ ] Update scraping scripts for site changes
- [ ] Compliance and legal review

---

## Contact Information for Data Access

### National Health Insurance Service (NHIS)
- **Address**: 32, Gonghang-daero, Wonju-si, Gangwon-do, Korea
- **Phone**: +82-33-736-0011
- **Email**: Available through official website
- **Data Requests**: http://nhiss.nhis.or.kr

### Ministry of Health and Welfare
- **Address**: 13 Doum-ro, Sejong Special Self-Governing City, Korea
- **Phone**: +82-44-202-2114
- **Website**: https://www.mohw.go.kr/eng/

### Health Insurance Review & Assessment Service
- **Address**: 60, Hyeoksin-ro, Wonju-si, Gangwon-do, Korea
- **Phone**: +82-33-739-0001
- **Business Portal**: https://biz.hira.or.kr/

---

*Last Updated: January 2025*
*Data Sources Current as of: December 2024*