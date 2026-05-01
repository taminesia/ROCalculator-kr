RO 계산기 스킬 파일 시스템 사용 설명서
개요
이제 this.DefaultDB_Skill은 JSON 파일에서 동적으로 로드되도록 변경되었으며, 다중 버전 스킬 전환을 지원합니다.

완료된 기능
1. 데이터 구조 변경
기존: LoadDB() 메서드 안에 하드코딩된 거대한 배열

현재: JSON 파일에서 동적으로 로드하여 버전 전환 지원

2. 추가된 Vue Data 속성
```javascript
data: {
    currentSkillFile: 'skills.json', // 현재스킬파일
    availableSkillFiles: ['skills.json', 'skills_new_version.json'], // 可用的技能檔案列表
}
```

### 3. 추가된 메서드

#### `loadSkillsFromJSON(filename)`
- **기능**：지정된 JSON 파일에서 스킬 데이터를 로드
- **매개변수**：filename（선택 사항, 기본값은 currentSkillFile）
- **반환값**：Promise<boolean>
- **오류처리**：로드 실패 시 자동으로 loadDefaultSkills() 예비 데이터를 사용

#### `switchSkillFile(filename)`
- **기능**：다른 스킬 파일로 전환
- **자동트리거**：직업 스킬 재필터링
- **UI 피드백**：성공/실패 메시지

#### `reloadSkills()`
- **기능**：현재 스킬 파일을 다시 로드
- **용도**：JSON 파일 수정 후 새로고침

#### `getSkillFileDisplayName(filename)`
- **기능**：스킬 파일의 표시 이름 가져오기
- **지원파일**：
  - `skills.json` → "원본스킬(Classic)"
  - `skills_new_version.json` → "신규버전스킬 (New Version)"
  - 기타 파일은 자동으로 .json 확장자를 제거

#### `loadDefaultSkills()`
- **기능**：기본 예비 스킬 데이터 로드
- **용도**：JSON 파일 로드 실패 시의 대체 방안

### 4. UI 컨트롤
스킬 목록 페이지 상단에 버전 선택기가 추가되었습니다：
- **드롭다운메뉴**：다른 버전의 스킬 파일 선택
- **새로고침버튼**：현재 파일을 다시 로드
- **상태표시**：로드된 스킬 수 표시 

## 사용방법

### 각기 다른 게임 버전을 위한 스킬 파일 생성

1. **기존파일복사**：
   ```bash
   cp skills.json skills_ep19.json
   ```

2. **스킬데이터수정**：
   - 스킬 배율 조정
   - 신규 스킬 추가
   - 스킬 속성 수정

3. **사용 가능한 파일 목록 업데이트**：
   ```javascript
   availableSkillFiles: [
       'skills.json', 
       'skills_new_version.json',
       'skills_ep19.json'  // 新增
   ]
   ```

4. **표시 이름 업데이트**（선택사항）：
   ```javascript
   getSkillFileDisplayName(filename) {
       const displayNames = {
           'skills.json': '원본스킬 (Classic)',
           'skills_new_version.json': '신규버전스킬 (New Version)',
           'skills_ep19.json': 'EP19 스킬 버전'  // 추가
       };
       return displayNames[filename] || filename.replace('.json', '');
   }
   ```

### JSON 파일 형식
```json
[
  {
    "skill": {
      "id": "RK_WINDCUTTER",
      "name": "윈드커터",
      "level": 5,
      "formula": "((WTI=='TwoHandedSword')?250:((WTI=='Spears')?400:300))*SLV*BLV/100",
      "class": "RK",
      "DamageTypeIdx": 0,
      "ranged": false,
      "critical": false,
      "cannon": false,
      "transWeaponDEF": false,
      "laterformula": false,
      "hitnumber": "(WTI=='TwoHandedSword')?2:1",
      "elemental": 0,
      "FCT": 0,
      "VCT": 0,
      "CD": 0.3,
      "GCD": 0.5,
      "Note": "양손검/창/기타 무기 장착 시 배율이 다름"
    }
  }
]
```

## 기술새부정보

### 로드 시점
- **초기화**：`LoadDB()` 메서드에서 자동으로 `loadSkillsFromJSON()` 호출
- **버전전환**：사용자가 UI를 통해 다른 파일을 선택할 때
- **수동새로고침**：새로고침 버튼을 클릭할 때

### 오류 처리
- 파일이 존재하지 않음：오류 메시지 표시, 예비 데이터 사용
- JSON 형식오류：오류 메시지 표시, 예비 데이터 사용
- 네트워크 오류：오류 메시지 표시, 예비 데이터 사용

### 직업 스킬 연동
스킬 파일이 로드된 후, 자동으로 `onChangeClass()` 가 트리거되어 현재 직업의 스킬을 다시 필터링합니다.

## 장점

1. **유지보수성**：스킬 데이터와 코드의 분리
2. **유연성**：다중 버전 전환 지원
3. **확장성**：새로운 버전 추가 용이
4. **하위 호환성**：하드코딩된 예비 데이터 보존
5. **사용자 친화적**：직관적인 스킬 버전 선택 인터페이스

## 주의사항

1. JSON 파일은 index.html 과 같은 폴더 않에 있어야 합니다. 
2. 파일명은 `availableSkillFiles` 배열에 추가해야하 합니다. 
3. JSON 형식이 정확해야 하며, 그렇지 않으면 예비 데이터를 사용하게 됩니다.
4. JSON 파일을 정기적으로 백업하는것을 권장합니다. 
