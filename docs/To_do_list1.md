@docs/To_do_list_report.md
1. 내가 궁극적으로 원하는 것은 @레포트_~~~ 의 계산 sheet 처럼 적정성 필드가 “위험” 인 사람을 알고 싶은거야
2. 내가 보니 이 적정성은 아래 계산 시트를 통해 계산 되.
3. 궁극적으로는 Template excel sheet가 없이도 download한 파일로만 프로그램으로 만들고 싶어


계산시트 분석
1. 소정근로 시간 : shiftee_data1.xls 의 G열
2. 승인된 근로시간 : shiftee_data1.xls 의 H열
3. 실제 근로시간 : shiftee_data1.xls 의 J열
4. 실제 근로시간 (결근,퇴근누락포함) : shiftee_data1.xls 의 J열 + W열 * 8 + X열 * 8: J열 - 실제 근로시간: W열 - 결근: X열 - 퇴근누락
5. 실제 근로시간(결근,퇴근누락 포함) 실제퇴근시간-출근등록시간 : =SUMPRODUCT((shiftee_data2!M$5:M$5000<>"")*((INT(shiftee_data2!M$5:M$5000*1440)/1440-INT(shiftee_data2!I$5:I$5000*1440)/1440)*24-shiftee데이타2!S$5:S$5000*24)*(shiftee_data2!B$5:B$5000=B10))+shiftee_data!W10*8+shiftee_data!X10*8
    a. shiftee_data2!M$5:M$5000<>"" -> M열이 빈칸이면 제외
    b. shiftee_data2!B$5:B$5000=B10 -> 현재 B열의 값을 기준으로 shitee_data2의 B열에서 해당하는 모든 값을 합산
    c. ((INT(M*1440)/1440 - INT(I*1440)/1440) * 24 - S*24) -> (종료시간 M − 시작시간 I)의 “근무시간(시간)” − S(휴게/제외시간, 시간)
6. 표준 근로시간 : shiftee_data1.xls 의 K열 + shiftee_data1.xls 의 T열
7. 표준 근로시간 (결근, 퇴근 누락포함) : shiftee_data1.xlsx의 K열 + shiftee_data1.xlsx의 W열 *8 + shiftee_data1의 X열*8 + shiftee_data1.xlsx의 T열
8. 유급휴가 시간 : shiftee_data1.xlsx 의 L열
9. 법정 근로시간 : D열 - K열
10. 실제 초과 근로시간 : IF((F10-L10)<0,0,F10-L10)
11. 실제 초과 근로시간 (결근, 퇴근누락 포함, 조기출근제외 : =IF(OR((H10-L10)>N10,H10>300),N10,IF((H10-L10)<0,0,H10-L10))
12. 조기 출근 합산 : =N10-O10
13. 법정 초과 근로시간 : =DAY($X$1)/7*10
14. 법규 위반 (전일까지) : =DAY($X$1)/7*12
15. 월법규 위반시간 : =12*4.3
16. 월말까지 가능한 초과근로 시간 : =IF((S10-O10)<0,"가능시간없음",S10-O10)
17. 적정성 : =IF(O10>Q10,"위험","정상")
18. 법규 기준초과자 : =IF(AND(O10<>0,O10>=R10),"법기준초과","")
