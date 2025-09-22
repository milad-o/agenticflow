from agenticflow.agents.supervisor.group_chat import GroupChatSupervisor


def test_group_chat_builds_chain():
    sup = GroupChatSupervisor(agent_task_type="chat")
    wf = sup.build_workflow(participants=["a1","a2"], rounds=2, topic="T")
    # Expect 4 tasks total, each depends on all prior
    assert len(wf.tasks) == 4
    ids = [t.task_id for t in wf.tasks]
    for i, t in enumerate(wf.tasks):
        expect_deps = set(ids[:i])
        assert t.dependencies == expect_deps
