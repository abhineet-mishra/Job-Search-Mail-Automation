import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("Third Party Risk Assessment");
  const [location, setLocation] = useState("Bangalore India OR remote");
  const [jobResults, setJobResults] = useState([]);
  const [systemStatus, setSystemStatus] = useState("Loading...");

  // Fetch system status
  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        const response = await axios.get(`${API}/`);
        setSystemStatus(response.data.message);
      } catch (error) {
        console.error("Error checking system status:", error);
        setSystemStatus("System Error");
      }
    };

    checkSystemStatus();
    fetchJobResults();
  }, []);

  // Fetch recent job results
  const fetchJobResults = async () => {
    try {
      const response = await axios.get(`${API}/job-results`);
      setJobResults(response.data);
    } catch (error) {
      console.error("Error fetching job results:", error);
    }
  };

  // Manual job search
  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/search-jobs`, {
        query: searchQuery,
        location: location,
        days_filter: 1
      });
      setJobs(response.data.jobs);
    } catch (error) {
      console.error("Error searching jobs:", error);
      alert("Error searching jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Send test email
  const sendTestEmail = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/send-test-email`);
      alert("Test email sent successfully!");
    } catch (error) {
      console.error("Error sending test email:", error);
      alert("Failed to send test email. Please check the logs.");
    } finally {
      setLoading(false);
    }
  };

  // Trigger manual search
  const triggerManualSearch = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/trigger-manual-search`);
      alert("Manual search completed! Check your email for results.");
      fetchJobResults();
    } catch (error) {
      console.error("Error triggering manual search:", error);
      alert("Failed to trigger manual search. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            TPRM Job Search Automation
          </h1>
          <p className="text-xl text-gray-600 mb-4">
            Automated Third Party Risk Assessment Job Search for Bangalore & Remote Positions
          </p>
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full">
            <div className="w-3 h-3 bg-green-400 rounded-full mr-2 animate-pulse"></div>
            Status: {systemStatus}
          </div>
        </div>

        {/* Control Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">Control Panel</h2>
          
          {/* Search Section */}
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Query
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Third Party Risk Assessment"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Bangalore India OR remote"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleSearch}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                {loading ? "Searching..." : "Search Jobs"}
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4">
            <button
              onClick={sendTestEmail}
              disabled={loading}
              className="bg-green-600 text-white py-2 px-6 rounded-md hover:bg-green-700 disabled:bg-gray-400 transition-colors"
            >
              Send Test Email
            </button>
            <button
              onClick={triggerManualSearch}
              disabled={loading}
              className="bg-purple-600 text-white py-2 px-6 rounded-md hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
            >
              Trigger Manual Search
            </button>
          </div>
        </div>

        {/* Automation Info */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Automation Schedule</h2>
          <div className="bg-blue-50 p-4 rounded-md">
            <div className="flex items-center mb-2">
              <div className="w-4 h-4 bg-blue-500 rounded-full mr-3"></div>
              <span className="font-medium">Daily Search: 9:00 AM IST</span>
            </div>
            <div className="flex items-center mb-2">
              <div className="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
              <span className="font-medium">Email: ananya4bh@gmail.com</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-orange-500 rounded-full mr-3"></div>
              <span className="font-medium">Filter: Last 24 hours, Bangalore & Remote positions</span>
            </div>
          </div>
        </div>

        {/* Current Search Results */}
        {jobs.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Current Search Results ({jobs.length} jobs)
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full table-auto">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Job Title</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Company</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Link</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Keywords</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Skills</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id} className="border-t hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-900">{job.job_title}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{job.company_name}</td>
                      <td className="px-4 py-2 text-sm">
                        <a
                          href={job.job_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          View Job
                        </a>
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-500">
                        {job.keywords.join(", ")}
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-500">
                        {job.technical_skills.join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent Search History */}
        {jobResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Recent Search History</h2>
            <div className="space-y-4">
              {jobResults.map((result, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-gray-900">{result.search_query}</h3>
                      <p className="text-sm text-gray-600">
                        {new Date(result.search_date).toLocaleDateString()} - {result.total_count} jobs found
                      </p>
                    </div>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                      {result.total_count} jobs
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
                <span className="text-lg font-medium">Processing...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;