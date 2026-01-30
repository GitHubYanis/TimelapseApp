import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  timestamp = new Date().getTime();

  refresh() {
    this.timestamp = new Date().getTime();
  }
}
