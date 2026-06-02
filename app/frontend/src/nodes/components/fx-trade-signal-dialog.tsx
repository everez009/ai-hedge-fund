import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface FxTradeSignalDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  outputNodeData: any;
  connectedAgentIds?: string[];
}

export function FxTradeSignalDialog({
  isOpen,
  onOpenChange,
  outputNodeData,
}: FxTradeSignalDialogProps) {
  // Parse the trade signals from output data
  let signals: any[] = [];
  try {
    if (outputNodeData?.messages && outputNodeData.messages.length > 0) {
      const lastMessage = outputNodeData.messages[outputNodeData.messages.length - 1];
      if (lastMessage?.content) {
        const parsed = typeof lastMessage.content === 'string' 
          ? JSON.parse(lastMessage.content)
          : lastMessage.content;
        
        // Extract signals from the parsed output
        if (parsed.signals && typeof parsed.signals === 'object') {
          signals = Object.entries(parsed.signals).map(([ticker, signal]: [string, any]) => ({
            ticker,
            ...signal,
          }));
        }
      }
    }
  } catch (error) {
    console.error('Failed to parse FX trade signals:', error);
  }

  const getDirectionColor = (direction: string) => {
    switch (direction.toLowerCase()) {
      case 'long':
        return 'text-green-600 bg-green-50';
      case 'short':
        return 'text-red-600 bg-red-50';
      case 'wait':
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>FX Trade Signals</DialogTitle>
        </DialogHeader>
        
        <div className="max-h-[60vh] overflow-y-auto">
          <div className="space-y-4 p-4">
            {signals.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No trade signals available
              </div>
            ) : (
              signals.map((signal) => (
                <div
                  key={signal.ticker}
                  className="rounded-lg border border-border p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">{signal.ticker}</h3>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getDirectionColor(
                        signal.direction
                      )}`}
                    >
                      {signal.direction.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <div className="text-xs text-muted-foreground">Entry Price</div>
                      <div className="font-mono text-sm font-semibold">
                        {signal.entry_price?.toFixed(5)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Stop Loss</div>
                      <div className="font-mono text-sm text-red-600">
                        {signal.stop_loss?.toFixed(5)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Take Profit</div>
                      <div className="font-mono text-sm text-green-600">
                        {signal.take_profit?.toFixed(5)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Confidence</div>
                      <div className="font-mono text-sm font-semibold">
                        {signal.confidence}%
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xs text-muted-foreground">Risk/Reward Ratio</div>
                      <div className="font-mono text-sm">
                        {signal.risk_reward_ratio?.toFixed(1)}:1
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Position Size</div>
                      <div className="font-mono text-sm">
                        {signal.position_size_pct}% of equity
                      </div>
                    </div>
                  </div>

                  {signal.reasoning && (
                    <div className="pt-2 border-t border-border">
                      <div className="text-xs text-muted-foreground mb-1">Reasoning</div>
                      <div className="text-sm">{signal.reasoning}</div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
