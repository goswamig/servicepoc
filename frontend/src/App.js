import React from 'react';
import './App.css';

class JobList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      jobs: [],
      selectedJob: null,
      newName: '',
      newModel: '',
    };
    this.handleInputChange = this.handleInputChange.bind(this);
    this.createJob = this.createJob.bind(this);
  }

  componentDidMount() {
    this.refreshJobList();
    this.timer = setInterval(() => this.refreshJobList(), 5000);
  }

  componentWillUnmount() {
    clearInterval(this.timer);
  }

  refreshJobList() {
    fetch('http://localhost:8000/jobs')
      .then(response => response.json())
      .then(data => this.setState({ jobs: data }));
  }

  stopJob(jobId) {
    fetch(`http://localhost:8000/jobs/${jobId}/stop`, {
      method: 'PUT'
    })
    .then(() => this.refreshJobList());
  }

  deleteAllJobs() {
    fetch(`http://localhost:8000/jobs`, {
      method: 'DELETE'
    })
    .then(() => this.refreshJobList());
  }

  describeJob(jobId) {
    fetch(`http://localhost:8000/jobs/${jobId}`)
      .then(response => response.json())
      .then(data => {
        this.setState({ selectedJob: data });
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  }

  createJob(event) {
    event.preventDefault();

    const { newName, newModel } = this.state;
    fetch('http://localhost:8000/jobs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({name: newName, model: newModel})
    })
    .then(() => {
      this.setState({
        newName: '',
        newModel: '',
      });
      this.refreshJobList();
    });
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }

  render() {
    const { jobs, selectedJob, newName, newModel } = this.state;

    return (
      <div>
        <h2>Jobs</h2>
        <form onSubmit={this.createJob}>
          <input
            name="newName"
            type="text"
            value={newName}
            onChange={this.handleInputChange}
            placeholder="Job name"
            required
          />
          <input
            name="newModel"
            type="text"
            value={newModel}
            onChange={this.handleInputChange}
            placeholder="Model"
            required
          />
          <input type="submit" value="Create Job" />
        </form>
        <button className="deleteButton" onClick={() => this.deleteAllJobs()}>Delete All Jobs</button>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Model</th>
              <th>Key</th>
              <th>Data File</th>
              <th>Output File</th>
              <th>Status</th>
              <th>Logs</th> {/* Added new log column */}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job, i) => (
              <tr key={i}>
                <td>{job.id}</td>
                <td>{job.name}</td>
                <td>{job.model}</td>
                <td>{job.key}</td>
                <td>{job.data_file}</td>
                <td>{job.out_file}</td>
                <td>{job.status}</td>
                <td>
                  {/* Log hyperlink */}
                  <a href={`http://localhost:8001/logs/${job.name}_${job.id}.json`} target="_blank" rel="noopener noreferrer">
                    View Logs
                  </a>
                </td>
                <td>
                  <button className="actionButton" onClick={() => this.describeJob(job.id)}>Describe</button>
                  <button className="actionButton" onClick={() => this.stopJob(job.id)}>Stop</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {selectedJob && 
          <div>
            <h3>Job Details:</h3>
            <pre>{JSON.stringify(selectedJob, null, 2)}</pre>
          </div>
        }
      </div>
    );
  }
}

function App() {
  return (
    <div className="App">
      <JobList />
    </div>
  );
}

export default App;

