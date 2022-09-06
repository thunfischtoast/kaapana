import { VisualizationsSetup } from 'src/plugins/visualizations/public/';

// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface WorkflowTriggerPluginSetup {}
// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface WorkflowTriggerPluginStart {}

export interface WorkflowTriggerSetupDependencies {
    visualizations: VisualizationsSetup;
}

export interface WorkflowTriggerOptionProps {
    fontSize: number;
    margin: number;
    buttonTitle: string;
}
