"""
Interactive Chatbot
===================

User-friendly wrapper for RAGAgent that provides interactive conversation features,
session management, and a rich set of commands for exploring knowledge and managing conversations.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .rag_agent import RAGAgent
from .config import ChatbotConfig, ConversationMode, CitationStyle
from .knowledge import RetrievalResult


class InteractiveChatbot:
    """
    Interactive wrapper for RAGAgent with conversation management and user-friendly features.
    
    Features:
    - Interactive conversation loop
    - Rich command system (help, stats, search, etc.)
    - Session persistence and management
    - Knowledge exploration tools
    - Performance monitoring
    - Customizable responses and behavior
    """
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.rag_agent: Optional[RAGAgent] = None
        
        # Conversation state
        self.session_id = self._generate_session_id()
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_active = False
        self.start_time = time.time()
        
        # Statistics
        self.stats = {
            'total_exchanges': 0,
            'total_knowledge_retrievals': 0,
            'average_response_time': 0.0,
            'session_duration': 0.0
        }
        
        # Commands
        self._setup_commands()
    
    def _setup_commands(self):
        """Setup the command system."""
        self.commands = {
            'help': self._cmd_help,
            'quit': self._cmd_quit,
            'exit': self._cmd_quit,
            'bye': self._cmd_quit,
            'stats': self._cmd_stats,
            'history': self._cmd_history,
            'clear': self._cmd_clear,
            'knowledge': self._cmd_knowledge,
            'search': self._cmd_search,
            'sources': self._cmd_sources,
            'config': self._cmd_config,
            'debug': self._cmd_debug,
            'examples': self._cmd_examples,
            'export': self._cmd_export,
            'retrieval': self._cmd_retrieval_stats,
            'session': self._cmd_session,
            'newsession': self._cmd_new_session,
            'restart': self._cmd_restart,
            'agents': self._cmd_agents,
            'delegate': self._cmd_delegate
        }
    
    async def start(self) -> None:
        """Initialize and start the chatbot."""
        print("🤖 Initializing chatbot...")
        
        # Create and start RAG agent
        self.rag_agent = RAGAgent(self.config)
        await self.rag_agent.start()
        
        self.is_active = True
        print(f"✅ Chatbot '{self.config.name}' ready!")
        
        # Display welcome message
        self._display_welcome()
    
    async def stop(self) -> None:
        """Stop the chatbot and cleanup."""
        if self.rag_agent:
            await self.rag_agent.stop()
        
        self.is_active = False
        self.stats['session_duration'] = time.time() - self.start_time
        
        print(f"\n👋 Chatbot session ended. Duration: {self.stats['session_duration']:.1f}s")
        self._display_final_stats()
    
    async def chat(self, message: str) -> str:
        """
        Process a single chat message and return the response.
        
        This method handles both regular queries and commands.
        """
        if not self.rag_agent:
            return "❌ Chatbot not initialized. Please call start() first."
        
        message = message.strip()
        if not message:
            return "Please enter a message."
        
        # Check if it's a command
        if message.lower().startswith('/') or message.lower() in self.commands:
            command = message.lower().lstrip('/')
            if command in self.commands:
                return await self.commands[command](message)
        
        # Process regular chat message
        start_time = time.time()
        
        try:
            # Execute with RAG agent
            result = await self.rag_agent.execute_task(message)
            
            if isinstance(result, dict):
                response = result.get('response', str(result))
                rag_metadata = result.get('rag_metadata', {})
                
                # Update statistics
                self._update_stats(start_time, rag_metadata)
                
                # Store conversation
                self._store_conversation(message, response, rag_metadata)
                
                return response
            else:
                response = str(result)
                self._store_conversation(message, response, {})
                return response
                
        except Exception as e:
            error_response = f"❌ I encountered an error: {str(e)}"
            self._store_conversation(message, error_response, {'error': str(e)})
            return error_response
    
    async def interactive_loop(self) -> None:
        """Run the interactive conversation loop."""
        if not self.is_active:
            await self.start()
        
        print("\n💬 Interactive mode started. Type '/help' for commands or '/quit' to exit.\n")
        
        try:
            while self.is_active:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Process message
                    response = await self.chat(user_input)
                    print(f"\n🤖 {self.config.name}: {response}\n")
                    print("-" * 60)
                    
                except KeyboardInterrupt:
                    print("\n\n⚡ Interrupted. Type '/quit' to exit gracefully.")
                    continue
                except EOFError:
                    print("\n\n👋 Session ended.")
                    break
                    
        finally:
            if self.is_active:
                await self.stop()
    
    def _display_welcome(self):
        """Display welcome message and instructions."""
        print("\n" + "=" * 70)
        print(f"🤖 {self.config.name}")
        if self.config.chatbot_personality:
            print(f"   {self.config.chatbot_personality}")
        print("=" * 70)
        
        # Display custom welcome message or default
        if self.config.welcome_message:
            print(f"\n{self.config.welcome_message}")
        else:
            print(f"\nWelcome! I'm {self.config.name}, your AI assistant.")
            if self.config.knowledge_sources:
                sources = [s.name for s in self.config.knowledge_sources]
                print(f"I have access to knowledge about: {', '.join(sources)}")
        
        print(f"\n💡 Knowledge Mode: {self.config.knowledge_mode.value}")
        print(f"📚 Citation Style: {self.config.citations.style.value}")
        print(f"💬 Conversation Mode: {self.config.conversation.mode.value}")
        
        print("\n🎯 Getting Started:")
        print("  • Ask me questions about my knowledge areas")
        print("  • Type '/help' to see all available commands")  
        print("  • Type '/examples' to see example questions")
        print("  • Type '/newsession' to start a fresh conversation")
        print("  • Type '/quit' to exit")
        print("=" * 70)
    
    def _display_final_stats(self):
        """Display final session statistics."""
        print("\n📊 Session Summary:")
        print(f"  💬 Total exchanges: {self.stats['total_exchanges']}")
        print(f"  🔍 Knowledge retrievals: {self.stats['total_knowledge_retrievals']}")
        if self.stats['total_exchanges'] > 0:
            print(f"  ⚡ Average response time: {self.stats['average_response_time']:.2f}s")
        print(f"  ⏱️  Session duration: {self.stats['session_duration']:.1f}s")
    
    def _update_stats(self, start_time: float, rag_metadata: Dict[str, Any]):
        """Update conversation statistics."""
        response_time = time.time() - start_time
        
        self.stats['total_exchanges'] += 1
        self.stats['total_knowledge_retrievals'] += rag_metadata.get('knowledge_chunks_used', 0)
        
        # Update average response time
        current_avg = self.stats['average_response_time']
        current_count = self.stats['total_exchanges']
        new_avg = ((current_avg * (current_count - 1)) + response_time) / current_count
        self.stats['average_response_time'] = new_avg
    
    def _generate_session_id(self) -> str:
        """Generate a new session ID."""
        timestamp = int(time.time())
        return f"session_{timestamp}"
    
    def _store_conversation(self, user_message: str, bot_response: str, metadata: Dict[str, Any]):
        """Store conversation exchange."""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'metadata': metadata
        }
        self.conversation_history.append(exchange)
    
    async def start_new_session(self, preserve_knowledge: bool = True) -> str:
        """Start a new conversation session."""
        old_session_id = self.session_id
        
        # Generate new session ID
        self.session_id = self._generate_session_id()
        
        # Reset conversation state
        self.conversation_history = []
        self.stats = {
            'total_exchanges': 0,
            'total_knowledge_retrievals': 0,
            'average_response_time': 0.0,
            'session_duration': 0.0
        }
        self.start_time = time.time()
        
        # Clear agent's memory if requested
        if self.rag_agent and hasattr(self.rag_agent, 'memory') and self.rag_agent.memory:
            try:
                await self.rag_agent.memory.clear()
            except Exception as e:
                print(f"Warning: Could not clear agent memory: {e}")
        
        return old_session_id
    
    async def restart_chatbot(self) -> None:
        """Restart the entire chatbot (useful for reloading knowledge)."""
        print("🔄 Restarting chatbot...")
        
        # Stop current agent
        if self.rag_agent:
            await self.rag_agent.stop()
        
        # Create and start new agent
        self.rag_agent = RAGAgent(self.config)
        await self.rag_agent.start()
        
        # Start new session
        await self.start_new_session()
        
        print("✅ Chatbot restarted successfully!")
    
    # Public session management methods
    def get_current_session_id(self) -> str:
        """Get the current session ID."""
        return self.session_id
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'duration': time.time() - self.start_time,
            'total_exchanges': self.stats['total_exchanges'],
            'total_knowledge_retrievals': self.stats['total_knowledge_retrievals'],
            'average_response_time': self.stats['average_response_time'],
            'conversation_entries': len(self.conversation_history)
        }
    
    # Command implementations
    async def _cmd_help(self, message: str) -> str:
        """Display help information."""
        help_text = f"""
🆘 **{self.config.name} Help**

**Basic Usage:**
  Just type your questions naturally. I'll search my knowledge base and provide helpful answers with citations.

**Available Commands:**
  `/help` or `/h`     - Show this help message
  `/quit` or `/exit`  - Exit the chatbot
  `/stats`           - Show conversation statistics
  `/history`         - Display conversation history
  `/clear`           - Clear conversation history
  `/knowledge`       - Show knowledge base summary
  `/search <query>`  - Search knowledge base directly
  `/sources`         - List all knowledge sources
  `/config`          - Show current configuration
  `/debug`           - Show debug information
  `/examples`        - Show example questions
  `/export`          - Export conversation history
  `/retrieval`       - Show retrieval statistics
  `/session`         - Show current session info
  `/newsession`      - Start a new conversation session
  `/restart`         - Restart the entire chatbot
  `/agents`          - Show available specialized agents
  `/delegate <query>` - Delegate task directly to specialized agents

**Knowledge Mode:** {self.config.knowledge_mode.value}
  - `hybrid`: Uses both knowledge base and general AI knowledge
  - `knowledge_first`: Tries knowledge base first, falls back to AI
  - `knowledge_only`: Only uses information from knowledge base
  - `llm_only`: Only uses general AI knowledge (no retrieval)

**Tips:**
  • Ask follow-up questions for more details
  • Be specific for better search results
  • Check sources in my responses for verification
        """
        return help_text.strip()
    
    async def _cmd_quit(self, message: str) -> str:
        """Quit the chatbot."""
        self.is_active = False
        return "👋 Goodbye! Thanks for chatting!"
    
    async def _cmd_stats(self, message: str) -> str:
        """Display conversation statistics."""
        current_duration = time.time() - self.start_time
        
        stats_text = f"""
📊 **Conversation Statistics**

**Current Session:**
  💬 Exchanges: {self.stats['total_exchanges']}
  🔍 Knowledge retrievals: {self.stats['total_knowledge_retrievals']}
  ⚡ Average response time: {self.stats['average_response_time']:.2f}s
  ⏱️  Session duration: {current_duration:.1f}s
  🆔 Session ID: {self.session_id}

**Configuration:**
  🧠 Knowledge mode: {self.config.knowledge_mode.value}
  📚 Citation style: {self.config.citations.style.value}
  💬 Conversation mode: {self.config.conversation.mode.value}
        """
        return stats_text.strip()
    
    async def _cmd_history(self, message: str) -> str:
        """Display conversation history."""
        if not self.conversation_history:
            return "📝 No conversation history yet."
        
        history_lines = ["📝 **Conversation History**\n"]
        
        for i, exchange in enumerate(self.conversation_history[-10:], 1):  # Last 10 exchanges
            timestamp = exchange['timestamp'][:19]  # Remove microseconds
            user_msg = exchange['user_message'][:100]  # Truncate long messages
            bot_msg = exchange['bot_response'][:100]
            
            history_lines.append(f"**{i}.** [{timestamp}]")
            history_lines.append(f"   👤 You: {user_msg}")
            history_lines.append(f"   🤖 Bot: {bot_msg}")
            history_lines.append("")
        
        if len(self.conversation_history) > 10:
            history_lines.insert(1, f"_(Showing last 10 of {len(self.conversation_history)} exchanges)_\n")
        
        return "\n".join(history_lines)
    
    async def _cmd_clear(self, message: str) -> str:
        """Clear conversation history."""
        count = len(self.conversation_history)
        self.conversation_history = []
        self.stats['total_exchanges'] = 0
        self.stats['total_knowledge_retrievals'] = 0
        self.stats['average_response_time'] = 0.0
        
        return f"🧹 Cleared {count} conversation exchanges and reset statistics."
    
    async def _cmd_knowledge(self, message: str) -> str:
        """Show knowledge base summary."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        try:
            summary = await self.rag_agent.get_knowledge_summary()
            
            knowledge_text = f"""
📚 **Knowledge Base Summary**

**Overview:**
  📄 Total documents: {summary.get('total_documents', 0)}
  📊 Total chunks: {summary.get('total_chunks', 0)}
  📏 Average chunk length: {summary.get('average_chunk_length', 0):.0f} characters

**Sources:**
            """
            
            sources = summary.get('sources', [])
            for source in sources:
                knowledge_text += f"\n  • {source}"
            
            document_types = summary.get('document_types', [])
            if document_types:
                knowledge_text += f"\n\n**Document Types:** {', '.join(document_types)}"
            
            return knowledge_text.strip()
            
        except Exception as e:
            return f"❌ Error getting knowledge summary: {e}"
    
    async def _cmd_search(self, message: str) -> str:
        """Search knowledge base directly."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        # Extract search query
        parts = message.split(' ', 1)
        if len(parts) < 2:
            return "❓ Please provide a search query. Example: `/search ocean creatures`"
        
        query = parts[1].strip()
        if not query:
            return "❓ Please provide a non-empty search query."
        
        try:
            results = await self.rag_agent.search_knowledge(query, max_results=5)
            
            if not results:
                return f"🔍 No results found for: '{query}'"
            
            search_text = [f"🔍 **Search Results for:** '{query}'\n"]
            
            for i, result in enumerate(results, 1):
                chunk = result.chunk_metadata
                preview = result.content[:150] + "..." if len(result.content) > 150 else result.content
                citation = result.get_citation("inline")
                
                search_text.append(f"**{i}.** {citation}")
                search_text.append(f"   Similarity: {result.similarity_score:.3f}")
                search_text.append(f"   Preview: {preview}")
                search_text.append("")
            
            return "\n".join(search_text)
            
        except Exception as e:
            return f"❌ Search failed: {e}"
    
    async def _cmd_sources(self, message: str) -> str:
        """List all knowledge sources."""
        if not self.config.knowledge_sources:
            return "📚 No knowledge sources configured."
        
        sources_text = ["📚 **Knowledge Sources**\n"]
        
        for i, source in enumerate(self.config.knowledge_sources, 1):
            sources_text.append(f"**{i}. {source.name}**")
            sources_text.append(f"   Path: {source.path}")
            sources_text.append(f"   Patterns: {', '.join(source.file_patterns)}")
            sources_text.append(f"   Chunk size: {source.chunk_size} chars")
            sources_text.append("")
        
        return "\n".join(sources_text)
    
    async def _cmd_config(self, message: str) -> str:
        """Show current configuration."""
        config_text = f"""
⚙️ **Current Configuration**

**Basic Settings:**
  🤖 Name: {self.config.name}
  🧠 Knowledge mode: {self.config.knowledge_mode.value}
  📚 Citation style: {self.config.citations.style.value}
  💬 Conversation mode: {self.config.conversation.mode.value}

**Knowledge Sources:** {len(self.config.knowledge_sources)}

**Retrieval Settings:**
  🔍 Strategy: {self.config.retrieval.strategy.value}
  🎯 Max attempts: {self.config.retrieval.max_attempts}
  📊 Min similarity: {self.config.retrieval.min_similarity}
  🔄 Sufficiency check: {self.config.retrieval.enable_sufficiency_check}

**Memory Settings:**
  📝 Max messages: {self.config.memory.max_messages}
  🧠 Memory type: {self.config.memory.type}
        """
        return config_text.strip()
    
    async def _cmd_debug(self, message: str) -> str:
        """Show debug information."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        debug_text = f"""
🐛 **Debug Information**

**Agent Info:**
  🆔 Agent ID: {self.rag_agent.agent_id}
  🏃 Running: {self.rag_agent._running}
  🧠 Memory type: {type(self.rag_agent.memory).__name__ if self.rag_agent.memory else 'None'}

**Last Retrieval:**
  📊 Results: {len(self.rag_agent.last_retrieval_results)}
  📋 Metadata: {self.rag_agent.last_retrieval_metadata}

**Session Info:**
  🆔 Session: {self.session_id}
  ⏰ Started: {datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S')}
  🗂️ History entries: {len(self.conversation_history)}
        """
        return debug_text.strip()
    
    async def _cmd_examples(self, message: str) -> str:
        """Show example questions."""
        examples_text = """
💡 **Example Questions**

**General Knowledge:**
  • "What are the main types of marine ecosystems?"
  • "Explain how photosynthesis works"
  • "Tell me about black holes and their properties"

**Specific Searches:**
  • "What adaptations help animals survive in the deep ocean?"
  • "How do different types of chemical reactions work?"
  • "What are the key stages of stellar evolution?"

**Follow-up Questions:**
  • "Can you give me more details about that?"
  • "What are some examples of this?"
  • "How does this relate to what we discussed earlier?"

**Commands:**
  • `/search quantum physics` - Direct knowledge search
  • `/sources` - See available knowledge sources
  • `/stats` - View conversation statistics

💭 **Tips:**
  • Ask follow-up questions for deeper exploration
  • Use specific terms for better search results
  • Check the citations in my responses for source verification
        """
        return examples_text.strip()
    
    async def _cmd_export(self, message: str) -> str:
        """Export conversation history."""
        if not self.conversation_history:
            return "📝 No conversation history to export."
        
        # Create export data
        export_data = {
            'session_id': self.session_id,
            'chatbot_name': self.config.name,
            'export_timestamp': datetime.now().isoformat(),
            'session_stats': self.stats.copy(),
            'conversation_history': self.conversation_history
        }
        
        # Save to file
        filename = f"conversation_{self.session_id}_{int(time.time())}.json"
        filepath = Path(filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return f"💾 Conversation exported to: {filepath.absolute()}"
            
        except Exception as e:
            return f"❌ Export failed: {e}"
    
    async def _cmd_retrieval_stats(self, message: str) -> str:
        """Show retrieval statistics."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        try:
            stats = await self.rag_agent.get_retrieval_stats()
            
            stats_text = f"""
🔍 **Retrieval Statistics**

**Last Retrieval:**
  📊 Results count: {stats['last_retrieval']['results_count']}
  📋 Metadata: {stats['last_retrieval']['metadata']}
            """
            
            if 'smart_retriever' in stats:
                sr_stats = stats['smart_retriever']
                stats_text += f"""

**Smart Retriever:**
  🎯 Total attempts: {sr_stats.get('total_attempts', 0)}
  ✅ Successful attempts: {sr_stats.get('successful_attempts', 0)}
  📊 Average results: {sr_stats.get('average_results', 0):.1f}
  🎯 Max similarity: {sr_stats.get('max_similarity', 0):.3f}
                """
            
            return stats_text.strip()
            
        except Exception as e:
            return f"❌ Error getting retrieval stats: {e}"
    
    async def _cmd_session(self, message: str) -> str:
        """Show current session information."""
        current_duration = time.time() - self.start_time
        
        session_text = f"""
🔖 **Session Information**

**Current Session:**
  🆔 Session ID: {self.session_id}
  ⏰ Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}
  ⏱️  Duration: {current_duration:.1f}s
  💬 Exchanges: {self.stats['total_exchanges']}
  🔍 Knowledge retrievals: {self.stats['total_knowledge_retrievals']}

**Agent Info:**
  🤖 Agent ID: {self.rag_agent.agent_id if self.rag_agent else 'Not initialized'}
  🧠 Memory entries: {len(self.conversation_history)}
  🏃 Agent running: {self.rag_agent._running if self.rag_agent else False}

**Session Management:**
  • `/newsession` - Start fresh conversation (clears history and memory)
  • `/restart` - Full restart (reloads knowledge base)
  • `/clear` - Clear current session history only
        """
        return session_text.strip()
    
    async def _cmd_new_session(self, message: str) -> str:
        """Start a new conversation session."""
        if not self.rag_agent:
            return "❌ Chatbot not initialized."
        
        try:
            old_session = await self.start_new_session()
            
            success_text = f"""
🆕 **New Session Started**

  ✅ Previous session ({old_session}) ended
  🆔 New session ID: {self.session_id}
  🧹 Conversation history cleared
  🧠 Agent memory cleared
  📊 Statistics reset
  ⏰ Session timer reset

💡 Your knowledge base is still available. You can now start a fresh conversation!
            """
            return success_text.strip()
            
        except Exception as e:
            return f"❌ Failed to start new session: {e}"
    
    async def _cmd_restart(self, message: str) -> str:
        """Restart the entire chatbot."""
        try:
            old_session = self.session_id
            await self.restart_chatbot()
            
            success_text = f"""
🔄 **Chatbot Restarted**

  ✅ Previous session ({old_session}) ended
  🆔 New session ID: {self.session_id}
  🧠 Agent fully restarted
  📚 Knowledge base reloaded
  💾 All caches refreshed
  📊 Statistics reset

💡 Everything is fresh and ready to go! Knowledge base has been reloaded.
            """
            return success_text.strip()
            
        except Exception as e:
            return f"❌ Failed to restart chatbot: {e}"
    
    async def _cmd_agents(self, message: str) -> str:
        """Show available specialized agents."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        if not self.rag_agent.multi_agent_enabled:
            return "🤖 Multi-agent delegation is disabled for this chatbot."
        
        if not self.rag_agent.specialized_agents:
            return "🤖 No specialized agents are currently available."
        
        agents_text = f"""
🤖 **Available Specialized Agents**

**Multi-Agent Status:** ✅ Enabled
**Total Agents:** {len(self.rag_agent.specialized_agents)}

**Active Agents:**
        """
        
        for agent_name, agent in self.rag_agent.specialized_agents.items():
            # Get agent info
            agent_info = self.config.specialized_agents.get(agent_name, {})
            description = agent_info.get('description', 'Specialized agent')
            keywords = self.config.task_routing_rules.get(agent_name, [])
            
            agents_text += f"""
  🎯 **{agent_name}**
    Description: {description}
    Status: ✅ Running
    Agent ID: {agent.agent_id}
    Keywords: {', '.join(keywords) if keywords else 'None configured'}
            """
        
        agents_text += """

💬 **Usage:**
  • Ask questions naturally - tasks will be auto-delegated based on keywords
  • Use `/delegate <query>` to force delegation
  • Regular questions without matching keywords use the main chatbot
        """
        
        return agents_text.strip()
    
    async def _cmd_delegate(self, message: str) -> str:
        """Delegate a task directly to specialized agents."""
        if not self.rag_agent:
            return "❌ RAG agent not initialized."
        
        if not self.rag_agent.multi_agent_enabled:
            return "❌ Multi-agent delegation is disabled."
        
        # Extract delegation query
        parts = message.split(' ', 1)
        if len(parts) < 2:
            return "❓ Please provide a query to delegate. Example: `/delegate analyze this data`"
        
        query = parts[1].strip()
        if not query:
            return "❓ Please provide a non-empty query to delegate."
        
        try:
            # Force delegation by calling the delegation method directly
            delegation_result = await self.rag_agent._try_delegate_task(query)
            
            if delegation_result:
                # Process the result as if it were a regular chat response
                response = delegation_result.get('response', str(delegation_result))
                delegation_metadata = delegation_result.get('delegation_metadata', {})
                
                # Store this interaction
                self._store_conversation(f"/delegate {query}", response, delegation_metadata)
                
                # Update stats
                start_time = time.time() - 1  # Approximate
                self._update_stats(start_time, delegation_metadata)
                
                return f"🤖 **Delegated to {delegation_metadata.get('delegated_to', 'specialized agent')}**\n\n{response}"
            else:
                suitable_agents = self.rag_agent._find_suitable_agents(query)
                if suitable_agents:
                    return f"❌ Delegation failed, but query matches keywords for: {', '.join(suitable_agents)}. Try rephrasing or check agent status."
                else:
                    return f"❌ No suitable agents found for query: '{query[:50]}...'. Available agents: {', '.join(self.rag_agent.specialized_agents.keys()) if self.rag_agent.specialized_agents else 'None'}"
        
        except Exception as e:
            return f"❌ Delegation failed: {e}"
    
    def __repr__(self) -> str:
        return f"InteractiveChatbot(name={self.config.name}, active={self.is_active})"
