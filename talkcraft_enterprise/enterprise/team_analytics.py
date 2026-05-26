from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("team_analytics")


class TeamAnalytics:
    def get_team_dashboard(self, team_id: int, db_session) -> Dict:
        from talkcraft_enterprise.database.models import Team, TeamMember, CollaborativeRoom
        team = db_session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {"error": "Team not found"}
        members = db_session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
        member_ids = [m.user_id for m in members]
        rooms = db_session.query(CollaborativeRoom).filter(
            CollaborativeRoom.host_user_id.in_(member_ids)
        ).all()
        total_sessions = len(rooms)
        completed = [r for r in rooms if r.ended_at]
        avg_duration = sum((r.ended_at - r.started_at).seconds for r in completed if r.started_at and r.ended_at) / max(1, len(completed))
        return {
            "team_name": team.name,
            "member_count": len(members),
            "total_sessions": total_sessions,
            "completed_sessions": len(completed),
            "avg_duration_seconds": round(avg_duration),
            "rooms_by_type": self._count_by_type(rooms),
            "recent_sessions": [
                {"name": r.name, "type": r.room_type, "status": r.status, "created_at": r.created_at.isoformat()}
                for r in sorted(rooms, key=lambda x: x.created_at, reverse=True)[:10]
            ],
        }

    def _count_by_type(self, rooms: List) -> Dict:
        counts = {}
        for r in rooms:
            t = r.room_type or "unknown"
            counts[t] = counts.get(t, 0) + 1
        return counts

    def get_organization_overview(self, org_id: int, db_session) -> Dict:
        from talkcraft_enterprise.database.models import Organization, Team, TeamMember, CollaborativeRoom
        org = db_session.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"error": "Organization not found"}
        teams = db_session.query(Team).filter(Team.organization_id == org_id).all()
        team_ids = [t.id for t in teams]
        all_members = db_session.query(TeamMember).filter(TeamMember.team_id.in_(team_ids)).all() if team_ids else []
        member_ids = [m.user_id for m in all_members]
        rooms = db_session.query(CollaborativeRoom).filter(
            CollaborativeRoom.host_user_id.in_(member_ids)
        ).all() if member_ids else []
        return {
            "organization": org.name,
            "plan": org.plan,
            "max_users": org.max_users,
            "team_count": len(teams),
            "total_members": len(all_members),
            "total_sessions": len(rooms),
            "teams": [self.get_team_dashboard(t.id, db_session) for t in teams],
            "recent_activity": len([r for r in rooms if r.status == "active"]),
        }

    def get_user_growth_metrics(self, user_id: int, db_session) -> Dict:
        from talkcraft_enterprise.database.models import CollaborativeRoom
        rooms = db_session.query(CollaborativeRoom).filter(
            CollaborativeRoom.host_user_id == user_id
        ).order_by(CollaborativeRoom.created_at).all()
        if not rooms:
            return {"available": False}
        scores = []
        for r in rooms:
            if r.status == "ended" and r.started_at and r.ended_at:
                duration = (r.ended_at - r.started_at).seconds
                scores.append({
                    "date": r.created_at.isoformat(),
                    "duration": duration,
                    "type": r.room_type,
                    "status": r.status,
                })
        return {
            "available": True,
            "total_rooms_hosted": len(rooms),
            "total_duration": sum(s["duration"] for s in scores),
            "sessions_by_type": self._count_by_type(rooms),
            "recent_activity": scores[-5:] if len(scores) >= 5 else scores,
        }

    def get_communication_growth(self, team_id: int, db_session) -> Dict:
        from talkcraft_enterprise.database.models import Team, TeamMember, CollaborativeRoom
        members = db_session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
        member_ids = [m.user_id for m in members]
        rooms = db_session.query(CollaborativeRoom).filter(
            CollaborativeRoom.host_user_id.in_(member_ids)
        ).order_by(CollaborativeRoom.created_at).all() if member_ids else []
        if len(rooms) < 2:
            return {"available": False}
        monthly = {}
        for r in rooms:
            month_key = r.created_at.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"sessions": 0, "total_duration": 0}
            monthly[month_key]["sessions"] += 1
            if r.started_at and r.ended_at:
                monthly[month_key]["total_duration"] += (r.ended_at - r.started_at).seconds
        return {
            "available": True,
            "monthly_growth": [
                {"month": k, "sessions": v["sessions"], "total_minutes": round(v["total_duration"] / 60, 1)}
                for k, v in sorted(monthly.items())
            ],
            "total_sessions": len(rooms),
            "total_participant_sessions": sum(r.get_state().get("participant_count", 0) for r in rooms),
        }


team_analytics = TeamAnalytics()
