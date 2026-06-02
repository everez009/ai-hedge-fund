import { useReactFlow, type NodeProps } from '@xyflow/react';
import { type ChangeEvent, useEffect } from 'react';
import { ChartLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useFlowContext } from '@/contexts/flow-context';
import { useLayoutContext } from '@/contexts/layout-context';
import { useNodeContext } from '@/contexts/node-context';
import { useFlowConnection } from '@/hooks/use-flow-connection';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useNodeState } from '@/hooks/use-node-state';
import { type FxAnalyzerNode } from '../types';
import { NodeShell } from './node-shell';

export function FxAnalyzerNode({
  data,
  selected,
  id,
  isConnectable,
}: NodeProps<FxAnalyzerNode>) {
  // Calculate default dates
  const today = new Date();
  const threeMonthsAgo = new Date(today);
  threeMonthsAgo.setMonth(today.getMonth() - 3);
  
  // Use persistent state hooks
  const [tickers, setTickers] = useNodeState(id, 'tickers', 'XAUUSD,GBPJPY,USDJPY');
  const [runMode] = useNodeState(id, 'runMode', 'single');
  // For live trading, use last 5 days. For backtest, use 3 months.
  const defaultStartDate = runMode === 'backtest' 
    ? threeMonthsAgo.toISOString().split('T')[0]
    : new Date(today.getTime() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useNodeState(id, 'startDate', defaultStartDate);
  const [endDate, setEndDate] = useNodeState(id, 'endDate', today.toISOString().split('T')[0]);
  
  const { currentFlowId } = useFlowContext();
  const nodeContext = useNodeContext();
  const { getAllAgentModels } = nodeContext;
  const { getNodes, getEdges } = useReactFlow();
  const { expandBottomPanel, setBottomPanelTab } = useLayoutContext();
  
  // Use the new flow connection hook
  const flowId = currentFlowId?.toString() || null;
  const {
    canRun,
    runFlow,
    runBacktest,
    stopFlow,
    recoverFlowState
  } = useFlowConnection(flowId);
  
  // Check if the hedge fund can be run
  const canRunHedgeFund = canRun && tickers.trim() !== '';
  
  // Add keyboard shortcut for Cmd+Enter / Ctrl+Enter to run hedge fund
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: 'Enter',
        ctrlKey: true,
        metaKey: true,
        callback: () => {
          if (canRunHedgeFund) {
            handlePlay();
          }
        },
        preventDefault: true,
      },
    ],
  });
  
  // Recover flow state when component mounts or flow changes
  useEffect(() => {
    if (flowId) {
      recoverFlowState();
    }
  }, [flowId, recoverFlowState]);
  
  const handleTickersChange = (e: ChangeEvent<HTMLInputElement>) => {
    setTickers(e.target.value);
  };

  const handleStartDateChange = (e: ChangeEvent<HTMLInputElement>) => {
    setStartDate(e.target.value);
  };

  const handleEndDateChange = (e: ChangeEvent<HTMLInputElement>) => {
    setEndDate(e.target.value);
  };

  const handleStop = () => {
    stopFlow();
  };

  const handlePlay = () => {
    // Expand bottom panel and set to output tab if backtest
    if (runMode === 'backtest') {
      expandBottomPanel();
      setBottomPanelTab('output');
    }
    
    // Get the current flow's nodes and edges
    const allNodes = getNodes();
    const allEdges = getEdges();
    
    // Find all nodes that are reachable from this node
    const reachableNodes = new Set<string>();
    const visited = new Set<string>();
    
    // DFS to find all reachable nodes
    const dfs = (nodeId: string) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      
      // If this is not the current node itself, add it to reachable nodes
      if (nodeId !== id) {
        reachableNodes.add(nodeId);
      }
      
      // Find all outgoing edges from this node
      const outgoingEdges = allEdges.filter(edge => edge.source === nodeId);
      for (const edge of outgoingEdges) {
        dfs(edge.target);
      }
    };
    
    // Start DFS from this node
    dfs(id);
    
    // Filter nodes to only include reachable ones
    const agentNodes = allNodes.filter(node => reachableNodes.has(node.id));
    
    // Filter edges to only include connections between reachable nodes (plus this node)
    const reachableNodeIds = new Set([id, ...reachableNodes]);
    const validEdges = allEdges.filter(edge => 
      reachableNodeIds.has(edge.source) && reachableNodeIds.has(edge.target)
    );

    // Collect agent models from all agent nodes
    const agentModels = [];
    const allAgentModels = getAllAgentModels(flowId);
    for (const node of agentNodes) {
      const model = allAgentModels[node.id];
      if (model) {
        agentModels.push({
          agent_id: node.id,
          model_name: model.model_name,
          model_provider: model.provider as any
        });
      }
    }
    
    // Convert tickers to array    
    const tickerList = tickers.split(',').map(t => t.trim());
    
    // Check if we're in backtest mode
    if (runMode === 'backtest') {
      // Use the flow connection hook to run the backtest with selected dates
      runBacktest({
        tickers: tickerList,
        // Send the actual graph structure instead of just selected agents
        graph_nodes: agentNodes.map(node => ({
          id: node.id,
          type: node.type,
          data: node.data,
          position: node.position
        })),
        graph_edges: validEdges,
        agent_models: agentModels,
        start_date: startDate,
        end_date: endDate,
        initial_capital: undefined,
        margin_requirement: 0.0, // Default margin requirement
        model_name: undefined,
        model_provider: undefined,
      });
    } else {
      // Use the regular hedge fund API for single run
      runFlow({
        tickers: tickerList,
        // Send the actual graph structure instead of just selected agents
        graph_nodes: agentNodes.map(node => ({
          id: node.id,
          type: node.type,
          data: node.data,
          position: node.position
        })),
        graph_edges: validEdges,
        agent_models: agentModels,
        start_date: startDate,
        end_date: endDate,
        model_name: undefined,
        model_provider: undefined,
      });
    }
  };

  return (
    <NodeShell
      id={id}
      name={data.name}
      description={data.description}
      selected={selected}
      isConnectable={isConnectable}
      icon={<ChartLine size={16} />}
      iconColor="text-blue-500"
    >
      <CardContent>
        <div className="space-y-2">
          <Input value={tickers} onChange={handleTickersChange} placeholder="XAUUSD,GBPJPY,USDJPY" />

          <div className="flex gap-2">
            <Input type="date" value={startDate} onChange={handleStartDateChange} />
            <Input type="date" value={endDate} onChange={handleEndDateChange} />
          </div>

          <div className="flex gap-2">
            <Button onClick={handlePlay} disabled={!canRunHedgeFund} size="sm">Run</Button>
            <Button variant="ghost" onClick={handleStop} size="sm">Stop</Button>
          </div>
        </div>
      </CardContent>
    </NodeShell>
  );
}
