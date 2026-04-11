type Scope = 'project' | 'conversation';

interface KnowledgeScopeTabBarProps {
  tab: Scope;
  conversationId?: string;
  onTabChange: (tab: Scope) => void;
}

export function KnowledgeScopeTabBar({
  tab,
  conversationId,
  onTabChange,
}: KnowledgeScopeTabBarProps) {
  return (
    <div className="knowledge-tabs" role="tablist" aria-label="Knowledge scope">
      <button
        role="tab"
        className={`knowledge-tab ${tab === 'project' ? 'active' : ''}`}
        aria-selected={tab === 'project'}
        onClick={() => onTabChange('project')}
      >
        Project
      </button>
      {conversationId && (
        <button
          role="tab"
          className={`knowledge-tab ${tab === 'conversation' ? 'active' : ''}`}
          aria-selected={tab === 'conversation'}
          onClick={() => onTabChange('conversation')}
        >
          Conversation
        </button>
      )}
    </div>
  );
}
