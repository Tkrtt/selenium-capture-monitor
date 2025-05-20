properties([
    parameters([
        // 1. Environment (Single Select)
        [
            $class: 'ChoiceParameter',
            name: 'ENVIRONMENT',
            description: 'Select target environment',
            choiceType: 'PT_SINGLE_SELECT',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: "return ['Dev', 'Test', 'Staging', 'Prod']",
                    sandbox: true
                ]
            ]
        ],

        // 2. Monitor Systems (Multi-Select)
        [
            $class: 'ChoiceParameter',
            name: 'MONITOR_SYSTEM',
            description: 'Select monitoring systems',
            choiceType: 'PT_CHECKBOX',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: "return ['Grafana', 'Dynatrace', 'Splunk']",
                    sandbox: true
                ]
            ]
        ],

        // 3. Monitor Servers (Dynamic based on Environment and Systems)
        [
            $class: 'CascadeChoiceParameter',
            name: 'MONITOR_SERVERS',
            description: 'Servers to monitor',
            referencedParameters: 'ENVIRONMENT,MONITOR_SYSTEM',
            choiceType: 'PT_CHECKBOX',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        def env = params.ENVIRONMENT
                        def systems = params.MONITOR_SYSTEM.split(',')
                        def servers = [
                            Dev: [
                                Grafana: ['grafana-dev1', 'grafana-dev2'],
                                Dynatrace: ['dynatrace-dev1'],
                                Splunk: ['splunk-dev1']
                            ],
                            Test: [
                                Grafana: ['grafana-test1', 'grafana-test2'],
                                Dynatrace: ['dynatrace-test1'],
                                Splunk: ['splunk-test1']
                            ]
                        ]
                        def selected = systems.collectMany { systems[env][it] }
                        return selected.flatten().unique()
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 4. Dashboards (Grafana)
        [
            $class: 'DynamicReferenceParameter',
            name: 'GRAFANA_DASHBOARDS',
            description: 'Grafana dashboards',
            referencedParameters: 'ENVIRONMENT,MONITOR_SYSTEM',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        if (!params.MONITOR_SYSTEM.contains('Grafana')) return []
                        def env = params.ENVIRONMENT
                        // Example API call (replace with actual)
                        def dashboards = [[value: '65ad655f...', display: 'New Dashboard']]
                        return groovy.json.JsonOutput.toJson(dashboards)
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 5. Dashboards (Dynatrace)
        [
            $class: 'DynamicReferenceParameter',
            name: 'DYNAATRACE_DASHBOARDS',
            description: 'Dynatrace dashboards',
            referencedParameters: 'ENVIRONMENT,MONITOR_SYSTEM',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        if (!params.MONITOR_SYSTEM.contains('Dynatrace')) return []
                        // Example API call
                        return groovy.json.JsonOutput.toJson([[value: 'dashboard-UUID', display: 'Default Dashboard']])
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 6. Dynatrace Environments
        [
            $class: 'DynamicReferenceParameter',
            name: 'DYNATRACE_ENVIRONMENTS',
            description: 'Dynatrace environments',
            referencedParameters: 'MONITOR_SYSTEM',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        if (!params.MONITOR_SYSTEM.contains('Dynatrace')) return []
                        // Fetch environments from API
                        return ['Env1', 'Env2']
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 7. Start Time
        [$class: 'DateTimeParameter', name: 'START_TIME', description: 'Start time'],

        // 8. End Time
        [$class: 'DateTimeParameter', name: 'END_TIME', description: 'End time'],

        // 9. Management Zone (Dynatrace)
        [
            $class: 'DynamicReferenceParameter',
            name: 'MANAGEMENT_ZONE',
            description: 'Dynatrace management zones',
            referencedParameters: 'DYNATRACE_ENVIRONMENTS',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        // Fetch zones based on environment
                        return ['Zone1', 'Zone2']
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 10. Datasources (Grafana)
        [
            $class: 'DynamicReferenceParameter',
            name: 'DATASOURCES',
            description: 'Grafana datasources',
            referencedParameters: 'ENVIRONMENT,MONITOR_SYSTEM',
            script: [
                $class: 'GroovyScript',
                script: [
                    script: '''
                        if (!params.MONITOR_SYSTEM.contains('Grafana')) return []
                        // Fetch datasources
                        return ['DS1', 'DS2']
                    ''',
                    sandbox: true
                ]
            ]
        ],

        // 11. Email Recipients
        [$class: 'TextParameter', name: 'MAIL_RECEIVERS', description: 'Email addresses (comma-separated)']
    ])
])

pipeline {
    agent any
    stages {
        stage('Process') {
            steps {
                script {
                    // Access parameters (example)
                    echo "Selected Dashboards: ${params.GRAFANA_DASHBOARDS}"
                }
            }
        }
    }
}
