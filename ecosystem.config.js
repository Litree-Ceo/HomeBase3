module.exports = {
  apps: [
    {
      name: 'HomeBase-Frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run dev',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'HomeBase-Backend',
      cwd: './backend',
      script: 'npm',
      args: 'run dev',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
