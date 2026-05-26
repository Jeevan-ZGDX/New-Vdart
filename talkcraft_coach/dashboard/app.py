import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import httpx
import json

COACH_API_URL = "http://localhost:8004"


def make_request(method, path, token=None, json_data=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{COACH_API_URL}{path}"
    try:
        with httpx.Client(timeout=10) as client:
            if method == "GET":
                r = client.get(url, headers=headers)
            elif method == "POST":
                r = client.post(url, headers=headers, json=json_data)
            else:
                return None
            if r.status_code == 200:
                return r.json()
    except Exception:
        return None
    return None


def metric_card(label, value, delta=None, color=None):
    delta_str = f"{delta:+.1f}%" if delta is not None else None
    st.metric(label=label, value=value, delta=delta_str)


def main():
    st.set_page_config(
        page_title="TalkCraft Coach",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: #e0e0e0; }
        .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #333; }
        .stMetric label { color: #888 !important; }
        .stMetric [data-testid="stMetricValue"] { color: #4CAF50 !important; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; margin: 2px; }
        .badge-unlocked { background-color: #1b4332; color: #4CAF50; border: 1px solid #4CAF50; }
        .badge-locked { background-color: #1e1e1e; color: #666; border: 1px solid #333; }
        .weakness-high { color: #f44336; }
        .weakness-medium { color: #FF9800; }
        .weakness-low { color: #FFC107; }
        .strength { color: #4CAF50; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎯 TalkCraft Coach")
    st.caption("Advanced Communication Intelligence & Personalized Coaching")

    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None

    sidebar = st.sidebar
    with sidebar:
        st.image("https://img.icons8.com/color/96/talk-male--v1.png", width=80)
        st.title("TalkCraft")

        if not st.session_state.token:
            tab1, tab2 = st.tabs(["Login", "Register"])
            with tab1:
                with st.form("login_form"):
                    l_user = st.text_input("Username")
                    l_pass = st.text_input("Password", type="password")
                    if st.form_submit_button("Login", use_container_width=True):
                        result = make_request("POST", "/api/auth/login", json_data={
                            "username": l_user, "password": l_pass,
                        })
                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
            with tab2:
                with st.form("register_form"):
                    r_user = st.text_input("Username*")
                    r_email = st.text_input("Email*")
                    r_pass = st.text_input("Password*", type="password")
                    r_name = st.text_input("Display Name")
                    if st.form_submit_button("Register", use_container_width=True):
                        result = make_request("POST", "/api/auth/register", json_data={
                            "username": r_user, "email": r_email,
                            "password": r_pass, "display_name": r_name,
                        })
                        if result:
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            st.rerun()
                        else:
                            st.error("Registration failed")
        else:
            user = st.session_state.user
            st.success(f"Welcome, {user.get('display_name', user['username'])}!")
            st.caption(f"Level: {user.get('skill_level', 'beginner').title()}")
            if st.button("Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.user = None
                st.rerun()

            st.divider()
            st.subheader("Navigation")
            page = st.radio("", [
                "Dashboard", "Progress", "Coaching", "Achievements",
                "Sessions", "Learning Paths",
            ], label_visibility="collapsed")
            st.session_state.page = page

    if not st.session_state.token:
        st.info("👋 Welcome to TalkCraft Coach! Please login or register to begin your communication improvement journey.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 📊 **Personalized Analytics**\nTrack your communication metrics over time with detailed progress charts.")
        with col2:
            st.markdown("### 🎯 **Adaptive Coaching**\nAI-powered coaching that adapts to your skill level and weaknesses.")
        with col3:
            st.markdown("### 🏆 **Achievements**\nEarn badges as you improve your communication skills.")
        return

    token = st.session_state.token
    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        _render_dashboard(token)
    elif page == "Progress":
        _render_progress(token)
    elif page == "Coaching":
        _render_coaching(token)
    elif page == "Achievements":
        _render_achievements(token)
    elif page == "Sessions":
        _render_sessions(token)
    elif page == "Learning Paths":
        _render_paths(token)


def _render_dashboard(token):
    st.header("📊 Dashboard Overview")
    data = make_request("GET", "/api/dashboard/overview", token=token)
    if not data:
        st.warning("Unable to load dashboard data")
        return

    summary = data.get("summary", {})
    weekly = data.get("weekly", {})
    weaknesses = data.get("weaknesses", {})
    trends = data.get("trends", {})
    coaching = data.get("coaching_focus", {})
    plan = data.get("improvement_plan")
    recs = data.get("daily_recommendations", [])
    achievements = data.get("achievements", {})
    weekly_chart = data.get("weekly_progress_chart", [])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Sessions", summary.get("total_sessions", 0),
                    summary.get("improvement_pct"))
    with col2:
        metric_card("Practice Time", f"{summary.get('total_practice_minutes', 0):.0f}m",
                    weekly.get("session_count", 0), "this week" if weekly.get("session_count") else None)
    with col3:
        metric_card("Avg Score", f"{summary.get('average_score', 0)*100:.0f}%")
    with col4:
        streak = summary.get("current_streak", {})
        metric_card("Streak", f"{streak.get('current', 0)} days",
                    streak.get("longest", 0), "best")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Weekly Progress")
        if weekly_chart:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[w["week"] for w in weekly_chart],
                y=[w["avg_score"] * 100 for w in weekly_chart],
                mode="lines+markers", name="Score",
                line=dict(color="#4CAF50", width=2),
            ))
            fig.add_trace(go.Scatter(
                x=[w["week"] for w in weekly_chart],
                y=[w["avg_confidence"] * 100 for w in weekly_chart],
                mode="lines+markers", name="Confidence",
                line=dict(color="#2196F3", width=2),
            ))
            fig.update_layout(
                template="plotly_dark", height=300, margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Week", yaxis_title="Score %",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete more sessions to see weekly progress")

    with col2:
        st.subheader("🎯 Current Focus Areas")
        focus = coaching.get("focus_areas", [])
        if focus:
            for area in focus:
                label = area.replace("_", " ").title()
                st.markdown(f"- ⚠️ **{label}**")
        else:
            st.info("Complete more sessions to identify focus areas")

        if plan:
            st.subheader("📋 Active Improvement Plan")
            st.markdown(f"**{plan['title']}**")
            st.progress(plan.get("progress_pct", 0) / 100)
            st.caption(f"Progress: {plan.get('progress_pct', 0):.0f}%")

    st.subheader("💪 Daily Recommendations")
    if recs:
        cols = st.columns(len(recs))
        for i, rec in enumerate(recs):
            with cols[i]:
                icon = "✅" if rec.get("completed") else "⚡"
                st.markdown(f"**{icon} {rec['title']}**")
                st.caption(f"{rec.get('duration_minutes', 5)} min | {rec.get('difficulty', 'beginner').title()}")
                if not rec.get("completed"):
                    st.button("Mark Done", key=f"rec_{rec['id']}", use_container_width=True)
    else:
        st.info("Generate daily recommendations from the Coaching page")

    st.subheader("🏆 Recent Achievements")
    recent = achievements.get("recent_unlocked", [])
    if recent:
        cols = st.columns(len(recent))
        for i, ach in enumerate(recent):
            with cols[i]:
                st.markdown(f"**{ach['title']}**")
                st.caption(ach['description'])
    else:
        st.info("Complete sessions to unlock achievements!")

    if weaknesses.get("available"):
        st.subheader("📉 Areas for Improvement")
        cols = st.columns(3)
        for i, w in enumerate(weaknesses.get("weaknesses", [])[:3]):
            with cols[i % 3]:
                sev = w.get("status", "fair")
                color = {"critical": "🔴", "weak": "🟡", "fair": "🟢"}.get(sev, "⚪")
                st.markdown(f"{color} **{w['label']}**: {w['average_score']*100:.0f}%")
                st.caption(f"Trend: {w.get('trend', 'stable')}")


def _render_progress(token):
    st.header("📈 Progress & Trends")

    col1, col2 = st.columns([1, 3])
    with col1:
        days = st.selectbox("Time Range", [7, 14, 30, 60, 90], index=2)

    trends = make_request("GET", f"/api/analytics/trends?days={days}", token=token)
    summary = make_request("GET", "/api/analytics/summary", token=token)
    weekly_progress = make_request("GET", "/api/analytics/weekly-progress", token=token)
    grammar = make_request("GET", "/api/analytics/grammar", token=token)

    if summary and summary.get("available"):
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("Current Score", f"{summary.get('latest_score', 0)*100:.0f}%",
                        summary.get('improvement_pct'))
        with col2:
            metric_card("Recent Avg", f"{summary.get('recent_average', 0)*100:.0f}%")
        with col3:
            metric_card("Total Sessions", summary.get("total_sessions", 0))

    if trends and trends.get("available"):
        st.subheader("Metric Trends")
        trend_data = trends.get("trends", {})
        dir_summary = trends.get("direction_summary", {})

        col1, col2, col3 = st.columns(3)
        improving = dir_summary.get("improving", [])
        declining = dir_summary.get("declining", [])
        if improving:
            with col1:
                st.markdown("**✅ Improving**")
                for m in improving[:3]:
                    st.markdown(f"- {m['label']} ({m['change']:+.1f}%)")
        if declining:
            with col2:
                st.markdown("**📉 Needs Attention**")
                for m in declining[:3]:
                    st.markdown(f"- {m['label']} ({m['change']:+.1f}%)")

        # Select metric to chart
        metrics = list(trend_data.keys())
        if metrics:
            selected = st.selectbox("Select Metric", metrics,
                                    format_func=lambda x: x.replace("_", " ").title())
            if selected in trend_data:
                td = trend_data[selected]
                values = td.get("values", [])
                if values:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=[v["date"] for v in values],
                        y=[v["value"] * 100 if selected != "average_wpm" else v["value"] for v in values],
                        mode="lines+markers",
                        line=dict(color="#4CAF50", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(76, 175, 80, 0.1)",
                    ))
                    fig.update_layout(
                        template="plotly_dark", height=400,
                        title=f"{selected.replace('_', ' ').title()} Trend",
                        xaxis_title="Date",
                        yaxis_title="Score (%)" if selected != "average_wpm" else "WPM",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        metric_card("Current", f"{td.get('current', 0)*100:.0f}%" if selected != "average_wpm" else f"{td.get('current', 0):.0f} WPM")
                    with col2:
                        metric_card("Average", f"{td.get('average', 0)*100:.0f}%" if selected != "average_wpm" else f"{td.get('average', 0):.0f} WPM")
                    with col3:
                        metric_card("Min", f"{td.get('min', 0)*100:.0f}%" if selected != "average_wpm" else f"{td.get('min', 0):.0f} WPM")
                    with col4:
                        metric_card("Direction", td.get("direction", "stable").title())

    if weekly_progress:
        st.subheader("📊 Weekly Progress Chart")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[w["week"] for w in weekly_progress],
            y=[w["sessions"] for w in weekly_progress],
            name="Sessions",
            marker_color="#4CAF50",
            yaxis="y",
        ))
        fig.add_trace(go.Scatter(
            x=[w["week"] for w in weekly_progress],
            y=[w["avg_score"] * 100 for w in weekly_progress],
            name="Avg Score",
            marker_color="#2196F3",
            yaxis="y2",
            mode="lines+markers",
        ))
        fig.update_layout(
            template="plotly_dark", height=350,
            yaxis=dict(title="Sessions", side="left"),
            yaxis2=dict(title="Score %", side="right", overlaying="y"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    if grammar and grammar.get("available"):
        st.subheader("📝 Grammar Improvement")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("Current Rate", f"{grammar.get('current_rate', 0)*100:.1f}%")
        with col2:
            metric_card("Improvement", f"{grammar.get('improvement_pct', 0):+.1f}%")
        with col3:
            st.markdown(f"**Trend:** {grammar.get('trend', 'stable').title()}")


def _render_coaching(token):
    st.header("🎯 Personalized Coaching")

    tab1, tab2, tab3, tab4 = st.tabs(["Focus", "Improvement Plan", "Daily Practice", "Difficulty"])

    with tab1:
        focus = make_request("GET", "/api/coaching/focus", token=token)
        if focus:
            st.subheader("Coaching Focus")
            style = focus.get("coaching_style", {})
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Difficulty:** {focus.get('difficulty', 'beginner').title()}")
                st.markdown(f"**Style:** {style.get('style', 'supportive').title()}")
                st.markdown(f"**Complexity:** {style.get('complexity', 'simple').title()}")
            with col2:
                st.markdown(f"**Feedback:** {style.get('feedback_frequency', 'frequent').title()}")
                st.markdown(f"**Encouragement:** {style.get('encouragement', 'high').title()}")
                st.markdown(f"**Trend:** {focus.get('trend', 'stable').title()}")

            st.markdown(f"*{style.get('description', '')}*")

            rec_mode = focus.get("recommended_mode", {})
            if rec_mode:
                st.info(f"💡 Recommended Mode: **{rec_mode.get('mode', '').replace('_', ' ').title()}** — {rec_mode.get('reason', '')}")

            weaknesses = focus.get("focus_areas", [])
            if weaknesses:
                st.subheader("Priority Focus Areas")
                for w in weaknesses:
                    st.markdown(f"- ⚠️ {w.replace('_', ' ').title()}")

            params = make_request("GET", "/api/coaching/parameters", token=token)
            if params:
                st.subheader("Conversation Parameters")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Temperature:** {params.get('temperature', 0.7)}")
                    st.markdown(f"**Max Tokens:** {params.get('max_tokens', 150)}")
                with col2:
                    st.markdown(f"**Topic Complexity:** {params.get('topic_complexity', 'simple').title()}")
                    st.markdown(f"**Response Length:** {params.get('response_length', 'short').title()}")
                with col3:
                    st.markdown(f"**Question Style:** {params.get('question_style', 'direct').replace('_', ' ').title()}")
                    st.markdown(f"**Feedback Detail:** {params.get('feedback_detail', 'high').title()}")

    with tab2:
        plan = make_request("GET", "/api/coaching/plan", token=token)
        if plan:
            st.subtitle(f"📋 {plan['title']}")
            st.markdown(plan.get("description", ""))
            st.progress(plan.get("progress_pct", 0) / 100)
            st.caption(f"Progress: {plan.get('progress_pct', 0):.0f}%")

            st.subheader("Focus Areas")
            for area in plan.get("focus_areas", []):
                st.markdown(f"- 🎯 **{area.get('label', area.get('area', '').replace('_', ' ').title())}**")

            st.subheader("Exercises")
            for ex in plan.get("exercises", []):
                with st.expander(f"{ex.get('name', 'Exercise')} ({ex.get('duration_minutes', 5)} min)"):
                    st.markdown(ex.get("description", ""))
                    st.caption(f"Difficulty: {ex.get('difficulty', 'beginner').title()} | Area: {ex.get('area', '').replace('_', ' ').title()}")

            if plan.get("recommendations"):
                st.subheader("Recommendations")
                st.markdown(plan["recommendations"])

            if st.button("Regenerate Plan", use_container_width=True):
                new_plan = make_request("POST", "/api/coaching/plan/generate", token=token)
                if new_plan:
                    st.success("New plan generated!")
                    st.rerun()

            if st.button("Complete Plan", use_container_width=True):
                make_request("POST", f"/api/coaching/plan/{plan['id']}/complete", token=token)
                st.success("Plan completed! Generating a new one...")
                st.rerun()
        else:
            st.info("No active improvement plan. Generate one to get started!")
            if st.button("Generate Plan", use_container_width=True):
                new_plan = make_request("POST", "/api/coaching/plan/generate", token=token)
                if new_plan:
                    st.success("Plan generated!")
                    st.rerun()

    with tab3:
        recs = make_request("GET", "/api/coaching/recommendations", token=token)
        if recs and len(recs) > 0:
            st.subheader("Today's Practice Recommendations")
            for rec in recs:
                col1, col2 = st.columns([4, 1])
                with col1:
                    icon = "✅" if rec.get("completed") else "⚡"
                    st.markdown(f"**{icon} {rec['title']}**")
                    st.caption(f"{rec.get('description', '')} — {rec.get('duration_minutes', 5)} min, {rec.get('difficulty', 'beginner').title()}")
                with col2:
                    if not rec.get("completed"):
                        if st.button("Done", key=f"daily_{rec['id']}", use_container_width=True):
                            make_request("POST", f"/api/coaching/recommendations/{rec['id']}/complete", token=token)
                            st.rerun()
                    else:
                        st.markdown("✅ **Completed**")
            if st.button("Generate New Recommendations", use_container_width=True):
                new_recs = make_request("POST", "/api/coaching/recommendations/generate", token=token)
                if new_recs:
                    st.success("New recommendations generated!")
                    st.rerun()
        else:
            st.info("No daily recommendations yet.")
            if st.button("Generate Recommendations", use_container_width=True):
                new_recs = make_request("POST", "/api/coaching/recommendations/generate", token=token)
                if new_recs:
                    st.success("Recommendations generated!")
                    st.rerun()

    with tab4:
        diff = make_request("GET", "/api/coaching/difficulty", token=token)
        if diff:
            st.subheader("Adaptive Difficulty")
            col1, col2, col3 = st.columns(3)
            with col1:
                metric_card("Current Level", diff.get("level", "beginner").title())
            with col2:
                metric_card("Trend", diff.get("trend", "stable").title())
            with col3:
                metric_card("Sessions Analyzed", diff.get("sessions_analyzed", 0))

            st.markdown(f"**Reason:** {diff.get('reason', 'N/A')}")
            if diff.get("changed"):
                st.success(f"🎉 Difficulty adapted from **{diff.get('previous_level', '').title()}** to **{diff.get('level', '').title()}**!")

            if diff.get("avg_recent_score") is not None:
                st.progress(min(1.0, diff["avg_recent_score"]))
                st.caption(f"Recent average score: {diff['avg_recent_score']*100:.0f}%")


def _render_achievements(token):
    st.header("🏆 Achievements")
    data = make_request("GET", "/api/achievements", token=token)

    if not data:
        st.warning("Unable to load achievements")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Unlocked", data.get("total_unlocked", 0))
    with col2:
        metric_card("Total", data.get("total_available", 0))
    with col3:
        metric_card("Progress", f"{data.get('progress_pct', 0):.0f}%")

    st.progress(data.get("progress_pct", 0) / 100)

    categories = data.get("categories", {})
    if categories:
        st.subheader("Categories")
        cols = st.columns(len(categories))
        for i, (cat, info) in enumerate(categories.items()):
            with cols[i % len(cols)]:
                st.markdown(f"**{cat.title()}**")
                st.markdown(f"{info['unlocked']}/{info['total']}")
                st.progress(info['unlocked'] / max(1, info['total']))

    badges = data.get("badges", [])
    if badges:
        st.subheader("All Badges")
        cols = st.columns(4)
        for i, badge in enumerate(badges):
            with cols[i % 4]:
                if badge["unlocked"]:
                    st.markdown(f"✅ **{badge['title']}**")
                    st.caption(badge["description"])
                else:
                    st.markdown(f"🔒 ~~{badge['title']}~~")
                    st.caption(badge["description"])

    if st.button("Check for New Achievements", use_container_width=True):
        result = make_request("POST", "/api/achievements/check", token=token)
        if result:
            new = result.get("new_achievements", [])
            if new:
                for a in new:
                    st.balloons()
                    st.success(f"🏆 New Achievement: **{a['title']}** — {a['description']}")
            else:
                st.info("No new achievements to unlock. Keep practicing!")


def _render_sessions(token):
    st.header("📋 Session History")

    sessions = make_request("GET", "/api/analytics/sessions?limit=50", token=token)
    if not sessions:
        st.info("No sessions recorded yet. Start practicing with TalkCraft!")
        return

    st.subheader(f"Recent Sessions ({len(sessions)})")

    for s in sessions:
        with st.expander(f"{s.get('date', '')[:10]} — Score: {s.get('scores', {}).get('overall', 0)*100:.0f}% — {s.get('mode', '')}"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                metric_card("Duration", f"{s.get('duration_minutes', 0):.0f}m")
                metric_card("WPM", f"{s.get('avg_wpm', 0):.0f}")
            with col2:
                metric_card("Filler Rate", f"{s.get('filler_rate', 0):.1f}%")
                metric_card("Grammar", f"{s.get('grammar_errors', 0)} errors")
            with col3:
                metric_card("Eye Contact", f"{s.get('eye_contact', 0):.0f}%")
                metric_card("Posture", f"{s.get('posture', 0):.0f}%")
            with col4:
                metric_card("Confidence", f"{s.get('confidence', 0):.0f}%")
                metric_card("Words", s.get("word_count", 0))

            strengths = s.get("strengths", [])
            weaknesses = s.get("weaknesses", [])
            if strengths:
                st.markdown("**Strengths:** " + ", ".join(f"{st['label']}" for st in strengths))
            if weaknesses:
                st.markdown("**Areas to Improve:** " + ", ".join(f"{w['label']} ({w['severity']})" for w in weaknesses[:3]))

    summary = make_request("GET", "/api/analytics/summary", token=token)
    if summary and summary.get("available"):
        st.subheader("Overall Summary")
        col1, col2 = st.columns(2)
        with col1:
            metric_card("Total Sessions", summary.get("total_sessions", 0))
            metric_card("Avg Score", f"{summary.get('average_score', 0)*100:.0f}%")
        with col2:
            metric_card("Total Practice", f"{summary.get('total_practice_minutes', 0):.0f}m")
            streak = summary.get("current_streak", {})
            metric_card("Streak", f"{streak.get('current', 0)}d / {streak.get('longest', 0)}d best")


def _render_paths(token):
    st.header("🗺️ Learning Paths")
    paths = make_request("GET", "/api/coaching/paths", token=token)

    if not paths:
        st.warning("Unable to load learning paths")
        return

    for p in paths:
        with st.expander(f"📚 {p['title']} — {p['topic_count']} topics ({', '.join(p.get('levels', []))})"):
            st.markdown(p.get("description", ""))
            path_detail = make_request("GET", f"/api/coaching/paths/{p['id']}", token=token)
            if path_detail:
                topics = path_detail.get("topics", {})
                for level, level_topics in topics.items():
                    st.markdown(f"**{level.title()} Level**")
                    for t in level_topics:
                        focus = t.get("focus", "")
                        focus_icon = {"clarity": "🎯", "confidence": "💪", "engagement": "💬",
                                      "filler_words": "🗣️", "speaking_pace": "⏱️",
                                      "posture": "🧍", "eye_contact": "👁️", "structure": "📐"}.get(focus, "📝")
                        st.markdown(f"- {focus_icon} **{t['name']}** ({t['duration_minutes']} min) — Focus: {focus.replace('_', ' ').title()}")


def run_dashboard():
    main()


if __name__ == "__main__":
    main()
