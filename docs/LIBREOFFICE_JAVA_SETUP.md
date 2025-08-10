# LibreOffice Java 설정 가이드

## 문제: "Could not create Java implementation loader"

LibreOffice 확장 프로그램 설치 시 이 오류가 발생하는 이유는 Java Runtime Environment(JRE)가 없거나 제대로 설정되지 않았기 때문입니다.

## 해결 방법

### 방법 1: Java 설치 (권장)

1. **Java 다운로드**
   - Oracle Java: https://www.java.com/download/
   - OpenJDK: https://adoptium.net/
   - 64비트 Windows라면 64비트 Java 설치 권장

2. **설치 확인**
   ```cmd
   java -version
   ```

### 방법 2: LibreOffice Java 설정

1. **LibreOffice 실행**
2. **도구 → 옵션** (Tools → Options)
3. **LibreOffice → 고급** (Advanced)
4. **Java 옵션 확인**:
   - "Java 런타임 환경 사용" 체크
   - 설치된 Java가 목록에 표시되는지 확인
   - 없다면 "추가" 버튼으로 Java 경로 지정

### 방법 3: Java 없이 진행 (대안)

H2Orestart가 Java를 반드시 요구하는 경우가 아니라면:

1. LibreOffice에서 Java 옵션 해제
2. 확장 프로그램 재설치 시도

### 일반적인 Java 설치 경로

- **Oracle Java**:
  - `C:\Program Files\Java\jre[version]`
  - `C:\Program Files (x86)\Java\jre[version]`

- **OpenJDK**:
  - `C:\Program Files\Eclipse Adoptium\jdk-[version]`
  - `C:\Program Files\OpenJDK\jdk-[version]`

## LibreOffice와 Java 호환성

- LibreOffice 32비트 → Java 32비트 필요
- LibreOffice 64비트 → Java 64비트 필요
- 버전 불일치 시 "Could not create Java implementation loader" 오류 발생

## 확인 사항

1. **LibreOffice 버전 확인**
   - 도움말 → LibreOffice 정보
   - 32비트/64비트 확인

2. **Java 버전 확인**
   ```cmd
   java -version
   ```

3. **환경 변수 확인**
   ```cmd
   echo %JAVA_HOME%
   echo %PATH%
   ```

## 대안: Java 없이 HWP 변환

Java 설치가 어려운 경우 다른 방법:

1. **한컴 오피스 2024 사용** (이미 설치됨)
2. **pyhwp 라이브러리** (Python)
3. **온라인 변환 서비스**

## 참고

- H2Orestart 확장이 반드시 Java를 요구하는지는 확장 프로그램 문서 확인 필요
- 일부 LibreOffice 확장은 Java 없이도 작동 가능
- LibreOffice Base 등 일부 기능은 Java 필수