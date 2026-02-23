import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { promisify } from 'util';

const execAsync = promisify(exec);
const fsPromises = fs.promises;

// Supported simulators
const SIMULATORS = {
  VERILOG: 'iverilog',
  VHDL: 'ghdl'
};

// Timeout for simulation (in milliseconds)
const SIMULATION_TIMEOUT = 30000; // 30 seconds

/**
 * Get the appropriate simulator for the given file
 * @param {string} filePath - Path to the design file
 * @returns {Object} - Simulator info {name, type}
 */
export function getSimulatorForFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  
  if (['.v', '.sv'].includes(ext)) {
    return { name: SIMULATORS.VERILOG, type: 'verilog' };
  } else if (['.vhd', '.vhdl'].includes(ext)) {
    return { name: SIMULATORS.VHDL, type: 'vhdl' };
  }
  
  throw new Error(`Unsupported file type: ${ext}`);
}

/**
 * Generate a testbench for the given circuit and test case
 * @param {Object} circuit - Circuit object
 * @param {Array} testCase - Test case inputs and expected outputs
 * @param {string} simulator - Simulator type ('iverilog' or 'ghdl')
 * @returns {string} - Generated testbench code
 */
function generateTestbench(circuit, testCase, simulator) {
  const { name, inputs, outputs } = circuit;
  const testName = `${name}_test_${Date.now()}`;
  
  if (simulator === SIMULATORS.VERILOG) {
    // Generate Verilog testbench
    return `
      module ${testName};
        // Inputs
        ${inputs.map((inp, i) => `reg ${inp.name};`).join('\n        ')}
        
        // Outputs
        ${outputs.map(out => `wire ${out.name};`).join('\n        ')}
        
        // Instantiate the Unit Under Test (UUT)
        ${name} uut (
          ${[...inputs, ...outputs].map(io => `.${io.name}(${io.name})`).join(',\n          ')}
        );
        
        initial begin
          // Initialize Inputs
          ${inputs.map((_, i) => `${inputs[i].name} = ${testCase.inputs[i]};`).join('\n          ')}
          
          // Wait for outputs to stabilize
          #10;
          
          // Display results
          $display("Inputs: ${inputs.map(i => `${i.name}=%b`).join(', ')}", ${inputs.map(i => i.name).join(', ')});
          $display("Outputs: ${outputs.map((o, i) => `${o.name}=%b (expected ${testCase.expectedOutputs[i]})`).join(', ')}", ${outputs.map(o => o.name).join(', ')});
          
          // Check outputs
          ${outputs.map((out, i) => 
            `if (${out.name} !== ${testCase.expectedOutputs[i]}) begin
              $display("Error: ${out.name} is %b, expected ${testCase.expectedOutputs[i]}", ${out.name});
              $finish;
            end`
          ).join('\n          ')}
          
          $display("Test passed!");
          $finish;
        end
      endmodule
    `;
  } else if (simulator === SIMULATORS.VHDL) {
    // Generate VHDL testbench
    return `
      library ieee;
      use ieee.std_logic_1164.all;
      
      entity ${testName} is
      end ${testName};
      
      architecture behavior of ${testName} is
        -- Component Declaration for the Unit Under Test (UUT)
        component ${name}
          port(
            ${[...inputs, ...outputs].map(io => 
              `${io.name} : ${io.name.includes('in') ? 'in' : 'out'} std_logic_vector(${io.bitWidth - 1} downto 0)`
            ).join(';\n            ')}
          );
        end component;
        
        -- Inputs
        ${inputs.map(inp => 
          `signal ${inp.name} : std_logic_vector(${inp.bitWidth - 1} downto 0) := (others => '0');`
        ).join('\n        ')}
        
        -- Outputs
        ${outputs.map(out => 
          `signal ${out.name} : std_logic_vector(${out.bitWidth - 1} downto 0);`
        ).join('\n        ')}
        
      begin
        -- Instantiate the Unit Under Test (UUT)
        uut: ${name} port map (
          ${[...inputs, ...outputs].map(io => 
            `${io.name} => ${io.name}`
          ).join(',\n          ')}
        );
        
        -- Stimulus process
        stim_proc: process
        begin          
          -- Apply inputs
          ${inputs.map((inp, i) => 
            `${inp.name} <= "${testCase.inputs[i].toString(2).padStart(inp.bitWidth, '0')}";`
          ).join('\n          ')}
          
          -- Wait for outputs to stabilize
          wait for 10 ns;
          
          -- Check outputs
          ${outputs.map((out, i) => 
            `assert ${out.name} = "${testCase.expectedOutputs[i].toString(2).padStart(out.bitWidth, '0')}" 
              report "Test failed: ${out.name} = " & to_string(${out.name}) & 
              " (expected ${testCase.expectedOutputs[i].toString(2).padStart(out.bitWidth, '0')})"
              severity failure;`
          ).join('\n          ')}
          
          report "Test passed!" severity note;
          wait;
        end process;
      end;
    `;
  }
  
  throw new Error(`Unsupported simulator: ${simulator}`);
}

/**
 * Run a simulation for the given circuit and test case
 * @param {string} designFilePath - Path to the design file
 * @param {Object} circuit - Circuit object
 * @param {Object} testCase - Test case to run
 * @param {string} simulator - Simulator to use ('iverilog' or 'ghdl')
 * @returns {Promise<Object>} - Simulation results
 */
async function runSimulation(designFilePath, circuit, testCase, simulator) {
  const tempDir = path.join(process.cwd(), 'temp', uuidv4());
  const designFileName = path.basename(designFilePath);
  const testbenchFileName = `tb_${Date.now()}.${simulator === SIMULATORS.VERILOG ? 'v' : 'vhd'}`;
  const testbenchPath = path.join(tempDir, testbenchFileName);
  const designPath = path.join(tempDir, designFileName);
  
  try {
    // Create temp directory
    await fsPromises.mkdir(tempDir, { recursive: true });
    
    // Copy design file to temp directory
    await fsPromises.copyFile(designFilePath, designPath);
    
    // Generate and save testbench
    const testbench = generateTestbench(circuit, testCase, simulator);
    await fsPromises.writeFile(testbenchPath, testbench, 'utf8');
    
    let command, outputFile;
    const execOptions = {
      cwd: tempDir,
      timeout: SIMULATION_TIMEOUT,
      maxBuffer: 1024 * 1024 * 10 // 10MB buffer for output
    };
    
    // Prepare commands based on simulator
    if (simulator === SIMULATORS.VERILOG) {
      const vvpFile = 'simulation.vvp';
      command = `iverilog -o ${vvpFile} ${testbenchFileName} ${designFileName} && vvp ${vvpFile}`;
      outputFile = path.join(tempDir, 'waveform.vcd');
    } else if (simulator === SIMULATORS.VHDL) {
      command = `ghdl -a ${designFileName} && \
                ghdl -a ${testbenchFileName} && \
                ghdl -e ${circuit.name}_test && \
                ghdl -r ${circuit.name}_test --vcd=waveform.vcd`;
      outputFile = path.join(tempDir, 'waveform.vcd');
    } else {
      throw new Error(`Unsupported simulator: ${simulator}`);
    }
    
    // Run simulation
    const { stdout, stderr } = await execAsync(command, execOptions);
    
    // Check for waveform file
    let waveform = null;
    try {
      waveform = await fsPromises.readFile(outputFile, 'base64');
    } catch (e) {
      console.warn('No waveform file generated:', e.message);
    }
    
    return {
      success: true,
      stdout,
      stderr,
      waveform,
      testCase: {
        ...testCase,
        inputs: circuit.inputs.map((input, i) => ({
          name: input.name,
          value: testCase.inputs[i]
        })),
        outputs: circuit.outputs.map((output, i) => ({
          name: output.name,
          expected: testCase.expectedOutputs[i],
          actual: stdout.includes('Test passed') ? testCase.expectedOutputs[i] : null
        }))
      }
    };
    
  } catch (error) {
    return {
      success: false,
      error: error.message,
      stdout: error.stdout || '',
      stderr: error.stderr || '',
      testCase: {
        ...testCase,
        inputs: circuit.inputs.map((input, i) => ({
          name: input.name,
          value: testCase.inputs[i]
        })),
        outputs: circuit.outputs.map((output, i) => ({
          name: output.name,
          expected: testCase.expectedOutputs[i],
          actual: null,
          error: error.message
        }))
      }
    };
  } finally {
    // Clean up temp directory
    try {
      await fsPromises.rm(tempDir, { recursive: true, force: true });
    } catch (e) {
      console.error('Error cleaning up temp directory:', e);
    }
  }
}

/**
 * Simulate a circuit with the given design file and test cases
 * @param {string} designFilePath - Path to the design file
 * @param {Object} circuit - Circuit object with test cases
 * @returns {Promise<Array>} - Array of test results
 */
export async function simulateCircuit(designFilePath, circuit) {
  const simulator = getSimulatorForFile(designFilePath);
  const results = [];
  
  // Run each test case
  for (const testCase of circuit.testCases) {
    const result = await runSimulation(
      designFilePath,
      circuit,
      testCase,
      simulator.name
    );
    
    results.push(result);
  }
  
  return results;
}

export default {
  simulateCircuit,
  getSimulatorForFile
};
