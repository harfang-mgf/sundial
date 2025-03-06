import streamlit as st
from datetime import datetime, timedelta
from src.ephemerides import ephemerides, col_labels

st.sidebar.page_link("st_pages/welcome.py", label="(back)", icon=":material/home:")

with st.sidebar:
    st.write("Charts")
    frame = st.selectbox("time frame", ('year', 'month', 'day'))
    col = st.selectbox("plot which data colum?", {'(none)':''}|col_labels)
    chart = st.selectbox("more charts", ('(none)', 'analemma'))


if 'current_date' not in st.session_state:
    now = datetime.today().astimezone()
    st.session_state['current_date'] = now
else:
    now = st.session_state.current_date

if st.button('&lt;&lt;&lt;', help(f"previous {frame}")):
    match frame:
        case 'year':    now = now.replace(year=now.year-1)
        case 'month':   now = now.replace(month=now.month-1) if now.month>1 else now.replace(year=now.year-1, month=12)
        case 'day':     now = now - timedelta(-1)
    st.session_state.current_date = now
if st.button('&gt;&gt;&gt;', help(f"next {frame}")):
    match frame:
        case 'year':    now = now.replace(year=now.year+1)
        case 'month':   now = now.replace(month=now.month+1) if now.month<12 else now.replace(year=now.year+1, month=1)
        case 'day':     now = now - timedelta(1)
    st.session_state.current_date = now



st.title(now.strftime(dict(year='%Y',month='%Y-%m',day='%Y-%m-%d')[frame]))
sunpos = ephemerides(now, 46, -6, frame)



if chart == 'analemma':
    st.write('#### analemma')
    plt = st.scatter_chart(sunpos[['eqti', 'sela']], x='eqti', y='sela', 
                  x_label=col_labels['eqti'], y_label=col_labels['sela'])
    
elif col != '(none)':
    st.write('#### '+col_labels[col])
    st.line_chart(sunpos[['datetime', col]], x='datetime', y=col, y_label=col_labels[col])
else:
    st.dataframe(sunpos)

