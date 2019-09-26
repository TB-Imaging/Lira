import React, { Component } from 'react'; // import from react
import fs from 'fs';
import { render, Window, App, Button } from 'proton-native'; // import the proton-native components

class Example extends Component {
  render() { // all Components must have a render method
    return (
      <App> // you must always include App around everything
        <Window title="Proton Native Rocks!" size={{w: 800, h: 600}} menuBar={false}>
          <Button stretchy={true} onClick={() => fs.readFile('.babelrc', 'utf8', (err, contents) => {
              console.log(contents)
          })}>
            Button
          </Button>
        </Window>
      </App>
    );
  }
}

render(<Example />); // and finally render your main component
