import { SearchIcon, RefreshCw } from "lucide-react";
import React, { useState, useEffect } from "react";
import { Card, CardContent } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
// Removed unused table UI components
import { Tabs, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Button } from "../../components/ui/button";  
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  TooltipProps
} from 'recharts';
import { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

// API base URL - use relative path in production, localhost in development
const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:3001';

// Custom tooltip component for bar charts
const CustomTooltip = ({ active, payload }: TooltipProps<ValueType, NameType>) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-2 border border-gray-200 shadow-md rounded">
        <p className="font-medium">{data.fullDate}</p>
        <p className="text-[#8884d8]">Price: ${data.price.toFixed(2)}</p>
      </div>
    );
  }
  return null;
};

export const LightCover = (): JSX.Element => {
  // State for search input and selected product
  const [searchInput, setSearchInput] = useState("");
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState("today");
  const [priceData, setPriceData] = useState<any>(null);
  const [showAllGraphs, setShowAllGraphs] = useState(false);
  const [selectedStore, setSelectedStore] = useState<string | null>(null);

  // State for search history with price averages for different periods
  const [searchHistory, setSearchHistory] = useState<Array<{
    id: number;
    name: string;
    current_price: number;
    avg_7d?: number;
    avg_30d?: number;
    avg_365d?: number;
  }>>([]);

  // Fetch price data for the selected product and period
  const fetchPriceData = async (productId: number, period: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/products/${productId}/price_average?period=${period}`);
      if (!response.ok) {
        throw new Error('Failed to fetch price data');
      }
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error fetching price data:', err);
      setError('Failed to fetch price data');
      return null;
    }
  };

  // Update price data when product or period changes
  useEffect(() => {
    if (selectedProduct && selectedProduct.id) {
      const fetchData = async () => {
        setLoading(true);
        const data = await fetchPriceData(selectedProduct.id, selectedPeriod);
        setPriceData(data);
        setLoading(false);
      };
      
      fetchData();
    }
  }, [selectedProduct, selectedPeriod]);

  // Fetch data for all periods when showAllGraphs is true
  useEffect(() => {
    if (showAllGraphs && selectedProduct && selectedProduct.id) {
      const fetchAllPeriods = async () => {
        setLoading(true);
        const periods = ['today', 'week', 'month', 'year'];
        const allData = await Promise.all(
          periods.map(period => fetchPriceData(selectedProduct.id, period))
        );
        
        const result = periods.reduce((acc, period, index) => {
          acc[period] = allData[index];
          return acc;
        }, {} as Record<string, any>);
        
        setPriceData(result);
        setLoading(false);
      };
      
      fetchAllPeriods();
    }
  }, [showAllGraphs, selectedProduct]);

  // Handle search input change
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(e.target.value);
  };

  // Handle search submission
  const handleSearchSubmit = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchInput.trim()) {
      setLoading(true);
      setError(null);
      
      try {
        // First, check if product exists in the backend
        const response = await fetch(`${API_BASE_URL}/api/products/by-name?name=${encodeURIComponent(searchInput)}`);
        
        if (!response.ok) {
          // If product doesn't exist, create it
          console.log("Creating new product:", searchInput);
          setError("Scraping prices from multiple sources. This may take up to 30 seconds...");
          
          const createResponse = await fetch(`${API_BASE_URL}/api/products`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              name: searchInput,
              store: selectedStore
            }),
            // Extend timeout for web scraping
            signal: AbortSignal.timeout(60000)
          });
          
          if (!createResponse.ok) {
            const errorData = await createResponse.json();
            throw new Error(`Failed to create product: ${errorData.error || 'Unknown error'}`);
          }
          
          const newProduct = await createResponse.json();
          
          // Fetch price averages for different periods
          const weekData = await fetchPriceData(newProduct.id, 'week');
          const monthData = await fetchPriceData(newProduct.id, 'month');
          const yearData = await fetchPriceData(newProduct.id, 'year');
          
          const productWithAverages = {
            ...newProduct,
            avg_7d: weekData?.average_price || newProduct.current_price,
            avg_30d: monthData?.average_price || newProduct.current_price,
            avg_365d: yearData?.average_price || newProduct.current_price
          };
          
          setSelectedProduct(productWithAverages);
          setShowAllGraphs(false);
          setError(null); // Clear the "scraping" message
          
          // Update search history
          setSearchHistory(prevHistory => {
            const filtered = prevHistory.filter(p => p.id !== productWithAverages.id);
            return [productWithAverages, ...filtered].slice(0, 5);
          });
        } else {
          // If product exists, use it
          const product = await response.json();
          
          // Fetch price averages for different periods
          const weekData = await fetchPriceData(product.id, 'week');
          const monthData = await fetchPriceData(product.id, 'month');
          const yearData = await fetchPriceData(product.id, 'year');
          
          const productWithAverages = {
            ...product,
            avg_7d: weekData?.average_price || product.current_price,
            avg_30d: monthData?.average_price || product.current_price,
            avg_365d: yearData?.average_price || product.current_price
          };
          
          setSelectedProduct(productWithAverages);
          setShowAllGraphs(false);
          
          // Update search history
          setSearchHistory(prevHistory => {
            const filtered = prevHistory.filter(p => p.id !== productWithAverages.id);
            return [productWithAverages, ...filtered].slice(0, 5);
          });
        }
        
        // Clear the search input
        setSearchInput("");
      } catch (err: any) {
        console.error('Error searching for product:', err);
        setError(`Error: ${err.message || 'Failed to search for product'}`);
      } finally {
        setLoading(false);
      }
    }
  };

  // Format chart data for display
  const formatChartData = (data: any) => {
    if (!data || !data.prices) return [];
    
    // For single period view, return all price points
    return data.prices.map((item: any) => {
      const date = new Date(item.timestamp);
      let dateLabel;
      
      // Format date label based on selected period
      if (selectedPeriod === 'today') {
        // For today, show hour
        dateLabel = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else if (selectedPeriod === 'week') {
        // For week, show day name
        dateLabel = date.toLocaleDateString([], { weekday: 'short' });
      } else if (selectedPeriod === 'month') {
        // For month, show day of month
        dateLabel = date.toLocaleDateString([], { month: 'short', day: 'numeric' });
      } else {
        // For year, show month
        dateLabel = date.toLocaleDateString([], { month: 'short' });
      }
      
      return {
        date: dateLabel,
        price: item.price,
        fullDate: date.toLocaleDateString()
      };
    });
  };

  const handleTabChange = async (value: string) => {
    setSelectedPeriod(value);
    setShowAllGraphs(false);
    // Auto-refresh when switching to week or month
    if ((value === 'week' || value === 'month') && selectedProduct?.id) {
      await handleRefresh(value);
    }
  };

  // Removed unused handleShowAll to satisfy lint

  // Refresh product price data
  const handleRefresh = async (periodOverride?: string) => {
    if (!selectedProduct || !selectedProduct.id) return;
    
    try {
      setLoading(true);
      
      // Call the refresh endpoint to update the product price
      const refreshResponse = await fetch(`${API_BASE_URL}/api/products/${selectedProduct.id}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ store: selectedStore }),
      });
      
      if (!refreshResponse.ok) {
        throw new Error('Failed to refresh product price');
      }
      
      const updatedProduct = await refreshResponse.json();
      
      // Fetch price averages for different periods
      const weekData = await fetchPriceData(updatedProduct.id, 'week');
      const monthData = await fetchPriceData(updatedProduct.id, 'month');
      const yearData = await fetchPriceData(updatedProduct.id, 'year');
      
      const productWithAverages = {
        ...updatedProduct,
        avg_7d: weekData?.average_price || updatedProduct.current_price,
        avg_30d: monthData?.average_price || updatedProduct.current_price,
        avg_365d: yearData?.average_price || updatedProduct.current_price
      };
      
      setSelectedProduct(productWithAverages);
      
      // Fetch updated price data for the current selected period (allow override)
      const period = periodOverride ?? selectedPeriod;
      const data = await fetchPriceData(updatedProduct.id, period);
      setPriceData(data);
      
      // Update search history
      setSearchHistory(prevHistory => {
        const filtered = prevHistory.filter(p => p.id !== productWithAverages.id);
        return [productWithAverages, ...filtered].slice(0, 5);
      });
    } catch (err) {
      console.error('Error refreshing product price:', err);
      setError('Failed to refresh product price');
    } finally {
      setLoading(false);
    }
  };

  // Render the appropriate chart based on selected period and showAllGraphs
  const renderChart = () => {
    if (loading) {
      return <div className="text-center p-6">Loading...</div>;
    }
    
    if (error) {
      return <div className="text-center text-red-500 p-6">{error}</div>;
    }
    
    if (!priceData) {
      return <div className="text-center p-6">Select a product to see price data</div>;
    }
    
    if (showAllGraphs) {
      // Render all charts
      return (
        <div className="flex flex-col gap-4">
          {['today', 'week', 'month', 'year'].map(period => {
            const periodData = priceData[period];
            if (!periodData) return null;
            
            const chartData = formatChartData(periodData);
            const title = period === 'today' ? 'Today' : 
                         period === 'week' ? 'This Week' : 
                         period === 'month' ? 'This Month' : 'This Year';
            
            return (
              <div key={period} className="mt-2">
                <h3 className="text-lg font-medium mb-2">{title} - Avg: ${periodData.average_price.toFixed(2)}</h3>
                <div className="h-[150px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="price" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            );
          })}
        </div>
      );
    } else {
      // Render single chart
      const chartData = formatChartData(priceData);
      
      return (
        <div className="h-[200px] w-full">
          <h3 className="text-lg font-medium mb-2">
            Average Price: ${priceData.average_price.toFixed(2)}
          </h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="price" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }
  };

  return (
    <div className="bg-[#f8f9fd] flex flex-row justify-center w-full">
      <div className="bg-[#f8f9fd] overflow-hidden w-[1512px] h-auto min-h-[982px] relative">
        {/* Store buttons card */}
        <Card className="absolute w-[200px] h-[420px] top-60 left-[200px] shadow-[0px_4px_4px_#00000040] rounded-xl">
          <CardContent className="p-4 relative h-full">
            <h2 className="text-lg font-medium mb-4">Stores</h2>
            <div className="flex flex-col gap-3">
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Amazon' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Amazon')}
              >
                Amazon
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Apple' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Apple')}
              >
                Apple
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Best Buy' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Best Buy')}
              >
                Best Buy
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Walmart' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Walmart')}
              >
                Walmart
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Target' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Target')}
              >
                Target
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Samsung' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Samsung')}
              >
                Samsung
              </Button>
              <Button 
                variant="outline" 
                className={`w-full justify-start text-left h-10 ${selectedStore === 'Olive Young' ? 'bg-purple-300 text-purple-900 hover:bg-purple-400' : ''}`}
                onClick={() => setSelectedStore('Olive Young')}
              >
                Olive Young
              </Button>
            </div>
          </CardContent>
        </Card>

        <header className="absolute w-[271px] h-[52px] top-[46px] left-[621px] bg-transparent">
          <h1 className="absolute w-[269px] h-[52px] top-0 left-0 [font-family:'DM_Sans',Helvetica] font-bold text-text text-[40px] tracking-[0] leading-[normal] whitespace-nowrap">
            Find a Product
          </h1>
        </header>

        <div className="absolute top-[156px] left-[484px] w-[544px]">
          <div className="relative w-full">
            <Input
              className="h-9 bg-system-materialssm-l-thick rounded-[10px] pl-10"
              placeholder="Search for a product..."
              value={searchInput}
              onChange={handleSearch}
              onKeyDown={handleSearchSubmit}
              disabled={loading}
            />
            <SearchIcon className="absolute w-7 h-7 top-1 left-2 text-label-colorslc-l-secondary" />
          </div>
          {error && (
            <div className="mt-2 p-2 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}
        </div>

        <Card className="absolute w-[595px] h-[420px] top-60 left-[464px] shadow-[0px_4px_4px_#00000040] rounded-xl">
          <CardContent className="p-4 relative h-full">
            <div className="h-[23px] [font-family:'DM_Sans',Helvetica] font-normal text-text text-lg tracking-[0] leading-[normal]">
              {selectedProduct ? selectedProduct.name : "Search for a product"}
            </div>
            
            <div className="[font-family:'DM_Sans',Helvetica] font-medium text-text text-[28px] tracking-[0] leading-[normal] mb-4 flex items-center">
              {selectedProduct ? (
                <>
                  <span>${selectedProduct.current_price}</span>
                  <Button
                    onClick={() => handleRefresh()}
                    className="ml-3 h-8 px-3 bg-transparent hover:bg-gray-100 flex items-center gap-2"
                    disabled={loading}
                    aria-label="Refresh current product price"
                  >
                    <RefreshCw size={16} className={`text-gray-600 ${loading ? 'animate-spin' : ''}`} />
                    <span className="text-sm text-gray-700">Refresh Price</span>
                  </Button>
                </>
              ) : (
                "Enter a product"
              )}
            </div>

            {/* Chart content */}
            <div className="mt-4">
              {loading ? (
                <div className="flex justify-center items-center h-[200px]">
                  <div className="animate-pulse flex flex-col items-center">
                    <RefreshCw size={24} className="animate-spin text-gray-400 mb-2" />
                    <p className="text-gray-500">Loading price data...</p>
                  </div>
                </div>
              ) : (
                renderChart()
              )}
            </div>

            <div className="absolute bottom-0 left-0 right-0 border-t">
              <Tabs value={selectedPeriod} onValueChange={handleTabChange} className="w-full">
                <TabsList className="bg-transparent w-full justify-start gap-4 h-[50px] ml-16 rounded-none">
                  <TabsTrigger
                    value="today"
                    className="[font-family:'DM_Sans',Helvetica] font-normal text-text text-lg data-[state=active]:text-text data-[state=inactive]:text-label"
                  >
                    Today
                  </TabsTrigger>
                  <TabsTrigger
                    value="week"
                    className="[font-family:'DM_Sans',Helvetica] font-normal text-lg data-[state=active]:text-text data-[state=inactive]:text-label"
                  >
                    This Week
                  </TabsTrigger>
                  <TabsTrigger
                    value="month"
                    className="[font-family:'DM_Sans',Helvetica] font-normal text-lg data-[state=active]:text-text data-[state=inactive]:text-label"
                  >
                    This Month
                  </TabsTrigger>
                  <TabsTrigger
                    value="year"
                    className="[font-family:'DM_Sans',Helvetica] font-normal text-lg data-[state=active]:text-text data-[state=inactive]:text-label"
                  >
                    This Year
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardContent>
        </Card>

        <Card className="absolute w-[700px] h-[322px] top-[700px] left-[420px] shadow-[0px_4px_4px_#00000040] rounded-[38px]">
          <CardContent className="p-0 relative h-full">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-solid border-text h-[60px]">
                  <th className="text-left font-medium [font-family:'DM_Sans',Helvetica] text-text text-lg pl-8 w-1/3">Name</th>
                  <th className="text-left font-medium [font-family:'DM_Sans',Helvetica] text-text text-lg pl-2 w-[16%]">Today</th>
                  <th className="text-left font-medium [font-family:'DM_Sans',Helvetica] text-text text-lg pl-2 w-[16%]">7D</th>
                  <th className="text-left font-medium [font-family:'DM_Sans',Helvetica] text-text text-lg pl-2 w-[16%]">1M</th>
                  <th className="text-left font-medium [font-family:'DM_Sans',Helvetica] text-text text-lg pl-2 w-[16%]">1Y</th>
                </tr>
              </thead>
              <tbody>
                {searchHistory.length > 0 ? (
                  searchHistory.map((item) => (
                    <tr 
                      key={item.id} 
                      className="border-b border-solid cursor-pointer hover:bg-gray-100"
                      onClick={() => {
                        setSelectedProduct(item);
                        setShowAllGraphs(false);
                      }}
                    >
                      <td className="py-4 [font-family:'DM_Sans',Helvetica] font-normal text-text text-base pl-8 w-1/3">
                        {item.name}
                      </td>
                      <td className="py-4 [font-family:'DM_Sans',Helvetica] font-normal text-text text-base pl-2 w-[16%]">
                        ${item.current_price.toFixed(2)}
                      </td>
                      <td className="py-4 [font-family:'DM_Sans',Helvetica] font-normal text-text text-base pl-2 w-[16%]">
                        ${item.avg_7d ? item.avg_7d.toFixed(2) : "-"}
                      </td>
                      <td className="py-4 [font-family:'DM_Sans',Helvetica] font-normal text-text text-base pl-2 w-[16%]">
                        ${item.avg_30d ? item.avg_30d.toFixed(2) : "-"}
                      </td>
                      <td className="py-4 [font-family:'DM_Sans',Helvetica] font-normal text-text text-base pl-2 w-[16%]">
                        ${item.avg_365d ? item.avg_365d.toFixed(2) : "-"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-4 text-center [font-family:'DM_Sans',Helvetica] font-normal text-label text-base">
                      Search for products to see your history
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
